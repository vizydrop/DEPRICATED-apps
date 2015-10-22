import json
from tornado import gen

from tornado.httpclient import AsyncHTTPClient

from tornado.log import app_log

from .base_filter import GitHubRepositoryFilter
from vizydrop.sdk.source import StreamingDataSource, SourceSchema
from vizydrop.fields import *


class GitHubContributorsStatsSource(StreamingDataSource):
    class Meta:
        identifier = "contributors"
        name = "Weekly Contributions"
        tags = ["Contributors", "Weekly", "Source Code", ]
        description = "List of weekly contributors data"
        filter = GitHubRepositoryFilter

    class Schema(SourceSchema):
        date = DateField(name="Date")
        author = TextField(name="Author")
        additions = NumberField(name="Code Additions")
        deletions = NumberField(name="Code Deletions")
        commits = NumberField(name="Number of Commits")

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

        source_filter = GitHubRepositoryFilter(source_filter)

        if source_filter.repository is None:
            raise ValueError('required parameter projects missing')

        # first we grab our list of commits
        req = account.get_request("https://api.github.com/repos/{}/stats/contributors".format(source_filter.repository))
        app_log.info("Starting retrieval of weekly contribution data for account {}".format(account._id))
        resp = yield client.fetch(req)
        data = json.loads(resp.body.decode('utf-8'))

        # open our list
        cls.write('[')
        count = 0
        for user_data in data:
            # and parse through our weeks
            for week in user_data.get('weeks', []):
                obj = {
                    # week data is a Unix timestamp
                    'date': datetime.fromtimestamp(week['w']).isoformat(),
                    # and our user
                    'author': user_data['author']['login'],
                    # and our commit data
                    'additions': week['a'],
                    'deletions': week['d'],
                    'commits': week['c']
                }
                if count > 0:
                    cls.write(',')
                cls.write(json.dumps(obj))
                count += 1
        # close our list
        cls.write(']')
        app_log.info("Finished retrieving {} contribution data for {}".format(count, account._id))
