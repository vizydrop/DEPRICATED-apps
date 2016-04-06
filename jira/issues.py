import json

from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.log import app_log
from vizydrop.sdk.source import StreamingDataSource, SourceSchema, SourceFilter
from vizydrop.fields import *


class JIRAIssuesSourceFilters(SourceFilter):
    def get_project_options(account, **kwargs):
        client = AsyncHTTPClient()
        req = account.get_request("{}/rest/api/2/project".format(account.jira_url.rstrip('/')))
        response = yield client.fetch(req)
        response_object = json.loads(response.body.decode('utf-8'))
        ret = [{"title": proj['name'], "value": proj['key']} for proj in response_object]
        return ret

    def get_issue_type_options(account, **kwargs):
        client = AsyncHTTPClient()
        req = account.get_request("{}/rest/api/2/issuetype".format(account.jira_url.rstrip('/')))
        response = yield client.fetch(req)
        response_object = json.loads(response.body.decode('utf-8'))
        ret = [{"title": ': '.join([type['name'], type['description']]), "value": type['id']} for type in
               response_object]
        return ret

    def get_states_options(account, projects, **kwargs):
        options = {}
        if not isinstance(projects, list):
            projects = projects.split(',')
        for project in projects:
            client = AsyncHTTPClient()
            req = account.get_request("{}/rest/api/2/project/{}/statuses".format(account.jira_url.rstrip('/'), project))
            response = yield client.fetch(req)
            response_object = json.loads(response.body.decode('utf-8'))
            for item in response_object:
                for state in item['statuses']:
                    options[state['id']] = state['name']
        return [{'title': value, 'value': key} for key, value in options.items()]

    projects = MultiListField(name="Projects", description="JIRA project ID", optional=False,
                              get_options=get_project_options)
    issue_types = MultiListField(name="Issue Type", description="Issue type", optional=True,
                                 get_options=get_issue_type_options)
    states = MultiListField(name="States", description="States", optional=True, get_options=get_states_options)
    created = DateField(name="Created", description="Issues created on, before, or during", optional=True)
    resolved = DateField(name="Resolved", description="Issues resolved on, before, or during", optional=True)

    def get_jql(self):
        """
        Builds a JQL string based on the filter's fields
        :return: JQL string
        """
        jql_pieces = ['project in ({})'.format(','.join(self.projects))]
        if self.issue_types is not None:
            jql_pieces.append('issuetype in ({})'.format(','.join(self.issue_types)))
        if self.states is not None:
            jql_pieces.append('(status in ({}))'.format(','.join(
                ["{}".format(state) for state in self.states])))
        if self.created is not None:
            if isinstance(self.created, date):
                jql_pieces.append('created > {}'.format(self.created.isoformat()))
            elif isinstance(self.created, dict):
                if '_min' in self.created.keys():
                    jql_pieces.append('created > {}'.format(self.created['_min']))
                if '_max' in self.created.keys():
                    jql_pieces.append('created < {}'.format(self.created['_max']))
        if self.resolved is not None:
            if isinstance(self.resolved, date):
                jql_pieces.append('resolved > {}'.format(self.resolved.isoformat()))
            elif isinstance(self.created, dict):
                if '_min' in self.resolved.keys():
                    jql_pieces.append('resolved > {}'.format(self.resolved['_min']))
                if '_max' in self.resolved.keys():
                    jql_pieces.append('resolved < {}'.format(self.resolved['_max']))
        return ' and '.join(jql_pieces)


class JIRAIssuesSource(StreamingDataSource):
    class Meta:
        identifier = "issues"
        name = "Issues"
        tags = ["Issues", "Bugs", ]
        description = "List of issues"
        filter = JIRAIssuesSourceFilters

    class Schema(SourceSchema):
        id = IDField(name="Issue ID")
        key = TextField(name="Issue Key")
        project = TextField(name="Project", response_loc="fields-project-name")
        state = TextField(name="Issue State", response_loc="fields-status-name")
        summary = TextField(name="Issue summary", response_loc="fields-summary")
        progress = NumberField(name="Current progress", response_loc="fields-progress")
        issuetype = TextField(name="Issue type", response_loc="fields-issuetype-name")
        votes = NumberField(name="Number of votes", response_loc="fields-votes-votes")
        updated = DateTimeField(name="Last Updated", response_loc="fields-updated")
        created = DateTimeField(name="Create Date", response_loc="fields-created")
        description = TextField(name="Issue description", response_loc="fields-description")
        priority = TextField(name="Issue priority", response_loc="fields-priority-name")
        reporter = TextField(name="Reporter Name", response_loc="fields-reporter-name")

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        """
        Gathers card information from JIRA
        POST <JIRA>/rest/api/2/search
            -- data: JQL:
                {"jql":"project = <proj>","startAt":<skip>,"maxResults":<limit>,"fields":[<fields you want>]}
        """
        client = AsyncHTTPClient()

        source_filter = JIRAIssuesSourceFilters(source_filter)

        if source_filter.projects is None:
            raise ValueError('required parameter projects missing')

        app_log.info("Start retrieval of issues for account {}".format(account._id))
        uri = "{}/rest/api/2/search".format(account.jira_url.rstrip('/'))
        jql = {
            "jql": source_filter.get_jql(),
            "startAt": skip
        }
        page_limit = limit if limit is not None else 1000
        jql.update({"maxResults": page_limit})

        # start our list
        cls.write('[')
        count = 0

        while True:
            app_log.info("Next page for {}, retrieved {} thus far".format(account._id, count))
            req = account.get_request(uri, headers={"Content-Type": "application/json"},
                                      method="POST", body=json.dumps(jql))

            response = yield client.fetch(req)

            page_data = response.body.decode('utf-8')
            resp_obj = json.loads(page_data)

            for issue in resp_obj['issues']:
                if count > 0:
                    # if we aren't the first in the list, be sure we put our delimiter in
                    cls.write(',')

                this_issue = cls.format_data_to_schema(issue)
                cls.write(json.dumps(this_issue))
                count += 1

            # handle pagination
            if limit is not None and count >= limit:
                # we've taken more than our limit, no need to continue
                break
            if resp_obj['total'] > resp_obj['startAt'] + page_limit:
                # there is a next page
                new_start = resp_obj['startAt'] + page_limit
                jql.update({'startAt': new_start})
            else:
                # no new page, let's break
                break

        app_log.info("Finished retrieval of {} issues for {}".format(count, account._id))
        # be sure to close our array
        cls.write(']')
