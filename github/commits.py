import json
from datetime import timedelta
from tornado import gen

from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.log import app_log

from tornado.locks import BoundedSemaphore
from tornado.queues import Queue

from .base_filter import GitHubRepositoryDateFilter
from vizydrop.sdk.source import StreamingDataSource, SourceSchema
from vizydrop.utils import parse_link_header
from vizydrop.fields import *


# how many concurrent fetches can we do?
FETCH_CONCURRENCY = 10
# our maximum request time (in seconds)
MAXIMUM_REQ_TIME = 30


class GitHubCommitsSource(StreamingDataSource):
    class Meta:
        identifier = "commits"
        name = "Commits"
        tags = ["Commits", "Source Code", ]
        description = "List of commits"
        filter = GitHubRepositoryDateFilter

    class Schema(SourceSchema):
        date = DateField(name="Date of the commit")
        author = TextField(name="Author")
        added_files = NumberField(name="Added Files")
        deleted_files = NumberField(name="Deleted Files")
        modified_files = NumberField(name="Modified Files")
        additions = NumberField(name="Code Additions")
        deletions = NumberField(name="Code Deletions")

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        """
        Gathers commit information from GH
        GET https://api.github.com/repos/:owner/:repo/commits
        Header: Accept: application/vnd.github.v3+json
        """
        if not account or not account.enabled:
            raise ValueError('cannot gather information without a valid account')
        client = AsyncHTTPClient()

        source_filter = GitHubRepositoryDateFilter(source_filter)

        if source_filter.repository is None:
            raise ValueError('required parameter projects missing')

        default_headers = {"Content-Type": "application/json", "Accept": "application/vnd.github.v3+json"}

        # first we grab our list of commits
        uri = "https://api.github.com/repos/{}/commits".format(source_filter.repository)
        qs = source_filter.get_qs()
        if qs != '':
            uri = uri + '?' + qs
        app_log.info("Starting retrieval of commit list for account {}".format(account._id))
        if limit is not None and limit <= 100:
            # we can handle our limit right here
            uri += "?per_page={}".format(limit)
        elif limit is None:
            uri += "?per_page=100"  # maximum number per page for GitHub API
        taken = 0

        queue = Queue()
        sem = BoundedSemaphore(FETCH_CONCURRENCY)
        done, working = set(), set()

        while uri is not None:
            app_log.info(
                "({}) Retrieving next page, received {} commits thus far".format(account._id, taken))
            req = account.get_request(uri, headers=default_headers)
            response = yield client.fetch(req)

            page_data = json.loads(response.body.decode('utf-8'))
            taken += page_data.__len__()
            for item in page_data:
                queue.put(item.get('url', None))

            if limit is None or taken < limit:
                # parse the Link header from GitHub (https://developer.github.com/v3/#pagination)
                links = parse_link_header(response.headers.get('Link', ''))
                uri = links.get('next', None)
            else:
                break
        app_log.info("({}) Commit list retrieved, fetching info for {} commits".format(account._id, taken))

        if queue.qsize() > 500:
            raise HTTPError(413, 'too many commits')

        # open our list
        cls.write('[')

        # our worker to actually fetch the info
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
                response_data = json.loads(response.body.decode('utf-8'))
                obj = {
                    'date': response_data['commit']['author']['date'],
                    'author': response_data['commit']['author']['name'],
                    'added_files': [file for file in response_data['files'] if file['status'] == 'added'].__len__(),
                    'deleted_files': [file for file in response_data['files'] if file['status'] == 'deleted'].__len__(),
                    'modified_files': [file for file in response_data['files'] if file['status'] == 'modified'].__len__(),
                    'additions': response_data['stats']['additions'],
                    'deletions': response_data['stats']['deletions']
                }
                if done.__len__() > 0:
                    cls.write(',')
                cls.write(json.dumps(obj))
                done.add(current_url)
                app_log.info("Page {} downloaded".format(page_no))

            finally:
                queue.task_done()
                sem.release()

        @gen.coroutine
        def worker():
            while True:
                yield sem.acquire()
                fetch_url()

        # start our concurrency worker
        worker()
        try:
            # wait until we're done
            yield queue.join(timeout=timedelta(seconds=MAXIMUM_REQ_TIME))
        except gen.TimeoutError:
            app_log.warning("Request exceeds maximum time, cutting response short")
        finally:
            # close our list
            cls.write(']')
        app_log.info("Finished retrieving commits for {}".format(account._id))
