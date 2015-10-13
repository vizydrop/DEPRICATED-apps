from tornado import gen
from datetime import timedelta
import json

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.log import app_log

from tornado.locks import BoundedSemaphore
from tornado.queues import Queue

from vizydrop.sdk.source import StreamingDataSource, SourceSchema, SourceFilter
from vizydrop.fields import *



# what file extensions are we interested in
VALID_FILETYPES = ['txt', 'tsv', 'csv', 'dat', 'xls', 'xlsx']
# how many concurrent fetches can we do?
FETCH_CONCURRENCY = 10
# our maximum request time (in seconds)
MAXIMUM_REQ_TIME = 30

RESPONSE_SIZE_LIMIT = 10  # MB


class DropboxFileFilter(SourceFilter):
    def get_file_list(account, **kwargs):
        queue = Queue()
        sem = BoundedSemaphore(FETCH_CONCURRENCY)
        done, working = set(), set()
        data = []

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

                for file in response_data:
                    # be sure we're a valid file type and less than our maximum response size limit
                    if file['path'][-3:].lower() in VALID_FILETYPES \
                            and int(file['bytes']) < RESPONSE_SIZE_LIMIT * 1000000:
                        data.append({"title": file['path'].lstrip('/'), "value": file['path']})
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
            url = "https://api.dropbox.com/1/search/auto/?query={}&include_membership=true".format(file_type)
            queue.put(url)
        # start our concurrency worker
        worker()
        # wait until we're done
        yield queue.join(timeout=timedelta(seconds=MAXIMUM_REQ_TIME))
        app_log.info("Finished list retrieval. Found {} items.".format(data.__len__()))
        return sorted(data, key=lambda f: f['title'])

    file = TextField(name="Filename", description="Path to the file", optional=False, get_options=get_file_list)


class DropboxFileSource(StreamingDataSource):
    class Meta:
        identifier = "file"
        name = "File"
        tags = ["File", ]
        description = "Contents from a Datafile"
        filter = DropboxFileFilter

    class Schema(SourceSchema):
        pass

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        source_filter = DropboxFileFilter(source_filter)

        if source_filter.file is None:
            raise ValueError('required parameter file missing')

        app_log.info("Starting to retrieve file {} => {}".format(source_filter.file, account._id))

        client = AsyncHTTPClient()
        uri = "https://content.dropboxapi.com/1/files/auto/{}".format(source_filter.file.lstrip('/'))

        def stream_callback(chunk):
            cls.write(chunk)

        oauth_client = account.get_client()
        uri, headers, body = oauth_client.add_token(uri)
        req = HTTPRequest(uri, headers=headers, body=body, streaming_callback=stream_callback)
        yield client.fetch(req)
        app_log.info("File {} retrieved for account {}".format(source_filter.file, account._id))
