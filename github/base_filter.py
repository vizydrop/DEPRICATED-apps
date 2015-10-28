import json
from urllib.parse import urlencode
from datetime import date as date_type

from tornado.httpclient import AsyncHTTPClient

from vizydrop.sdk.source import SourceFilter
from vizydrop.fields import *
from vizydrop.utils import parse_link_header


class GitHubRepositoryFilter(SourceFilter):
    def get_repo_options(account, **kwargs):
        """
        Gathers repository options for GitHub commits source

        GET https://api.github.com/user/repos
        Special Accept header required: application/vnd.github.moondragon+json
        """
        client = AsyncHTTPClient()
        uri = "https://api.github.com/user/repos?per_page=100"
        data = []
        while uri is not None:
            req = account.get_request(uri, headers={"Accept": "application/vnd.github.moondragon+json"})
            response = yield client.fetch(req)
            response_object = json.loads(response.body.decode('utf-8'))
            data += response_object
            links = parse_link_header(response.headers.get('Link', ''))
            uri = links.get('next', None)
        return [{"title": repo['full_name'], "value": repo['full_name']}
                for repo in data]

    repository = TextField(name="Repository", description="GitHub Repository", optional=False,
                           get_options=get_repo_options)

    def get_qs(self, encode=True):
        return ""


class GitHubRepositoryDateFilter(SourceFilter):
    repository = TextField(name="Repository", description="GitHub Repository", optional=False,
                           get_options=GitHubRepositoryFilter.get_repo_options)
    date = DateField(name="Date", description="Date or range to focus on", optional=True)

    def get_qs(self, encode=True):
        filter_elements = {}
        if self.date:
            if isinstance(self.date, date_type):
                # chances are we won't get an actual date object from Hermione, but this is here in case...
                filter_elements['since'] = '{}T00:00:00Z'.format(self.date.isoformat())
            elif isinstance(self.date, dict):
                if '_min' in self.date.keys():
                    filter_elements['since'] = '{}T00:00:00Z'.format(self.date['_min'])
                if '_max' in self.date.keys():
                    filter_elements['until'] = '{}T00:00:00Z'.format(self.date['_max'])
            elif isinstance(self.date, str):
                filter_elements['since'] = '{}T00:00:00Z'.format(self.date)
        if not encode:
            return filter_elements
        if filter_elements.__len__() > 0:
            return "{}".format(urlencode(filter_elements))
        else:
            return ""
