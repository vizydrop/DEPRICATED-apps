import json
from tornado import gen

from tornado.httpclient import AsyncHTTPClient, HTTPError

from tornado.log import app_log

from .base_filter import GitHubRepositoryDateFilter
from vizydrop.sdk.source import StreamingDataSource, SourceSchema
from vizydrop.fields import *


class GitHubContributorsStatsSource(StreamingDataSource):
    class Meta:
        identifier = "contributors"
        name = "Weekly Contributions"
        tags = ["Contributors", "Weekly", "Source Code", ]
        description = "List of weekly contributors data"
        filter = GitHubRepositoryDateFilter

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

        source_filter = GitHubRepositoryDateFilter(source_filter)

        if source_filter.repository is None:
            raise ValueError('required parameter projects missing')

        data = None

        req = account.get_request("https://api.github.com/repos/{}/stats/contributors".format(source_filter.repository))
        app_log.info("Starting retrieval of weekly contribution data for account {}".format(account._id))
        for i in range(0, 3):  # we only try this four times at most
            resp = yield client.fetch(req)
            if (resp.code == 202):
                # GitHub is making this in the background, let's wait a little and retry
                app_log.info("GitHub responded 202: waiting for stats to compile for account {}".format(account._id))
                yield gen.sleep(5)
            else:
                data = json.loads(resp.body.decode('utf-8'))
                app_log.info("Data received for weekly contribution")
                break

        # if we didn't get anything from GitHub, we fail out
        if not data:
            app_log.warning("No contribution data received from GitHub for account {}".format(account._id))
            raise HTTPError(408, "request timed out: please try again later")

        # open our list
        cls.write('[')
        count = 0
        # bring up our min/max filters if we have them
        if isinstance(source_filter.date, dict):
            filter_min = source_filter.date.get('_min', None)
            filter_max = source_filter.date.get('_max', None)
            if filter_min is not None:
                try:
                    filter_min = datetime.strptime(filter_min, '%Y-%m-%d')
                except ValueError:
                    pass
            if filter_max is not None:
                try:
                    filter_max = datetime.strptime(filter_max, '%Y-%m-%d')
                except ValueError:
                    pass
        # otherwise, our dates come in as strings, so we need to parse that
        elif isinstance(source_filter.date, str):
            try:
                source_filter.date = datetime.strptime(source_filter.date, '%Y-%m-%d')
            except ValueError:
                pass
        for user_data in data:
            # and parse through our weeks
            for week in user_data.get('weeks', []):
                weekdate = datetime.fromtimestamp(week['w'])
                if source_filter.date is not None:
                    # check for filtered date
                    if filter_min is not None and filter_min > weekdate:
                        continue
                    if filter_max is not None and filter_max < weekdate:
                        continue
                    if isinstance(source_filter.date, datetime) and source_filter.date > weekdate:
                        continue
                obj = {
                    # week data is a Unix timestamp
                    'date': weekdate.isoformat(),
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
