import json
from datetime import timedelta

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.log import app_log
from tornado.locks import BoundedSemaphore, Condition
from tornado.queues import Queue
from vizydrop.sdk.source import StreamingDataSource, SourceSchema, SourceFilter
from vizydrop.fields import *


# what file extensions are we interested in
VALID_FILETYPES = ['txt', 'tsv', 'csv', 'dat', 'xls', 'xlsx']
# how many concurrent fetches can we do?
FETCH_CONCURRENCY = 10
# our maximum request time (in seconds)
MAXIMUM_REQ_TIME = 30


class OneDriveFileFilter(SourceFilter):
    def get_file_list(account, **kwargs):
        queue = Queue()
        sem = BoundedSemaphore(FETCH_CONCURRENCY)
        done, working = set(), set()
        data = []
        ids = set()

        @gen.coroutine
        def fetch_url():
            current_url = yield queue.get()
            try:
                if current_url in working:
                    return
                page_no = working.__len__()
                app_log.info("Fetching page {}".format(page_no))
                working.add(current_url)
                req = account.get_request(current_url)
                client = AsyncHTTPClient()
                response = yield client.fetch(req)
                done.add(current_url)
                app_log.info("Page {} downloaded".format(page_no))
                response_data = json.loads(response.body.decode('utf-8'))

                url = response_data.get('@odata.nextLink', None)
                if url is not None:
                    queue.put(url)

                for file in response_data.get('value', []):
                    if file['name'][-4:].strip('.').lower() in VALID_FILETYPES:
                        if file['id'] not in ids:
                            ids.add(file['id'])
                            data.append(
                                {"title": file['parentReference']['path'].split(':')[1].lstrip('/') + '/' + file['name'],
                                 "value": file['id']})
                app_log.info("Page {} completed".format(page_no))
            finally:
                queue.task_done()
                sem.release()

        @gen.coroutine
        def worker():
            while True:
                yield sem.acquire()
                fetch_url()

        app_log.info("Gathering filelist for account {}".format(account._id))
        for file_type in VALID_FILETYPES:
            file_type = '.'.join([file_type])
            url = "https://api.onedrive.com/v1.0/drive/root/view.search?top=1000&select=parentReference,name,id,size&q={}" \
                .format(file_type)
            queue.put(url)
        # start our concurrency worker
        worker()
        # wait until we're done
        yield queue.join(timeout=timedelta(seconds=MAXIMUM_REQ_TIME))
        app_log.info("Finished list retrieval. Found {} items.".format(data.__len__()))
        return sorted(data, key=lambda f: f['title'])

    file = TextField(name="Filename", description="Path to the file", optional=False, get_options=get_file_list)


class OneDriveFileSource(StreamingDataSource):
    class Meta:
        identifier = "file"
        name = "File"
        tags = ["File", ]
        description = "Contents from a Datafile"
        filter = OneDriveFileFilter

    class Schema(SourceSchema):
        pass

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        source_filter = OneDriveFileFilter(source_filter)

        if source_filter.file is None:
            raise ValueError('required parameter file missing')

        app_log.info("Starting to retrieve file for {}".format(account._id))

        client = AsyncHTTPClient()
        uri = "https://api.onedrive.com/v1.0/drive/items/{}/content".format(source_filter.file)
        lock = Condition()

        def crawl_url(url):
            # some yummy regex
            location_header_regex = re.compile(r'^Location:\s?(?P<uri>http:/{2}\S+)')
            http_status_regex = re.compile(r'^HTTP/[\d\.]+\s(?P<status>\d+)')
            receiving_file = False

            # define our callbacks
            def header_callback(header):
                m = http_status_regex.match(header)
                if m is not None:
                    # process our HTTP status header
                    status = m.group('status')
                    if int(status) == 200:
                        # if we're 200, we're receiving the file, not just a redirect
                        app_log.info("Receiving file {} for account {}".format(source_filter.file, account._id))
                        global receiving_file
                        receiving_file = True
                m = location_header_regex.match(header)
                if m is not None:
                    # process our location header
                    uri = m.group('uri')
                    # and grab _that_ url
                    app_log.info("Following redirect for file {}".format(source_filter.file))
                    crawl_url(uri)

            def stream_callback(chunk):
                # only dump out chunks that are of the file we're looking for
                global receiving_file
                if receiving_file:
                    app_log.info("Writing chunk of {}B".format(chunk.__len__()))
                    cls.write(chunk)

            def on_completed(resp):
                if 200 <= resp.code <= 299:
                    lock.notify()

            oauth_client = account.get_client()
            uri, headers, body = oauth_client.add_token(url)
            req = HTTPRequest(uri, headers=headers, body=body, header_callback=header_callback,
                              streaming_callback=stream_callback)
            client.fetch(req, callback=on_completed)

        crawl_url(uri)
        # wait for us to complete
        try:
            yield lock.wait(timeout=timedelta(seconds=MAXIMUM_REQ_TIME))
            app_log.info("File {} retrieved successfully".format(source_filter.file))
        except gen.TimeoutError:
            app_log.error("Request for file {} => {} timed out!".format(source_filter.file, account._id))