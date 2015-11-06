from urllib.parse import urlencode
import json
from tornado import gen

from tornado.httpclient import AsyncHTTPClient

from tornado.log import app_log

from .base_filter import GitHubRepositoryDateFilter
from vizydrop.utils import parse_link_header
from vizydrop.fields import *
from vizydrop.sdk.source import SourceSchema, StreamingDataSource


class GitHubIssuesFilter(GitHubRepositoryDateFilter):
    def get_milestone_options(account, repository, **kwargs):
        """
        Gathers milestone options for a GitHub repository
        """
        client = AsyncHTTPClient()
        uri = "https://api.github.com/repos/{}/milestones?page_size=100".format(repository)
        data = []
        while uri is not None:
            req = account.get_request(uri)
            response = yield client.fetch(req)
            response_object = json.loads(response.body.decode('utf-8'))
            data += response_object
            links = parse_link_header(response.headers.get('Link', ''))
            uri = links.get('next', None)
        return [{"title": "#{} - {}".format(milestone['number'], milestone['title']),
                 "value": milestone['number']}
                for milestone in data]

    state = TextField(name="Issue state", description="Filter issues by state", options=['open', 'closed', 'all'])
    milestone = NumberField(name="Milestone ID", description="ID number of a milestone",
                            get_options=get_milestone_options)

    def get_qs(self, encode=True):
        filter_elements = super().get_qs(encode=False)
        if self.state:
            filter_elements['state'] = self.state
        if self.milestone:
            filter_elements['milestone'] = self.milestone
        if not encode:
            return filter_elements
        if filter_elements.__len__() > 0:
            return "{}".format(urlencode(filter_elements))
        else:
            return ""


class GitHubIssuesSource(StreamingDataSource):
    class Meta:
        identifier = "issues"
        name = "Issues"
        tags = ["Issues", "Bugs", ]
        description = "List of GitHub issues"
        filter = GitHubIssuesFilter

    class Schema(SourceSchema):
        url = TextField(name="Permalink to the issue")
        number = IDField(name="Issue number", force_int=True)
        state = TextField(name="Issue state")
        title = TextField(name="Issue title")
        body = TextField(name="Issue body")
        created_at = DateField(name="Issue creation date")
        updated_at = DateField(name="Issue update date")
        comments = NumberField(name="Comment count")
        user = TextField(name="Name of the reporter", response_loc="user-login")
        assignee = TextField(name="Name of the assignee", response_loc="assignee-login")
        milestone = TextField(name="Milestone name", response_loc="milestone-title")

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

        source_filter = GitHubIssuesFilter(source_filter)

        if source_filter.repository is None:
            raise ValueError('required parameter projects missing')
        app_log.info("Starting retrieval of issues for {}".format(account._id))

        default_headers = {"Content-Type": "application/json", "Accept": "application/vnd.github.v3+json"}

        page_size = limit if limit is not None and limit <= 100 else 100
        taken = 0

        uri = "https://api.github.com/repos/{}/issues?per_page={}&{}".format(source_filter.repository,
                                                                             page_size, source_filter.get_qs())
        uri = uri.rstrip('&')  # remove trailing & in case filter has no QS elements

        cls.write('[')
        count = 0

        while uri is not None:
            app_log.info(
                "({}) Retrieving next page, received {} issues thus far".format(account._id, taken))
            req = account.get_request(uri, headers=default_headers)
            response = yield client.fetch(req)

            page_data = json.loads(response.body.decode('utf-8'))

            for issue in page_data:
                if count > 0:
                    cls.write(',')
                cls.write(cls.format_data_to_schema(issue))
                count += 1

            if limit is None or count < limit:
                # parse the Link header from GitHub (https://developer.github.com/v3/#pagination)
                links = parse_link_header(response.headers.get('Link', ''))
                uri = links.get('next', None)
            else:
                break

        cls.write(']')

        app_log.info("[GitHub] Finished retrieving {} issues for repository {}".format(count, source_filter.repository))
