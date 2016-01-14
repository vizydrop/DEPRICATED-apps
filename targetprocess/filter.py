import json

from tornado.httpclient import AsyncHTTPClient
from vizydrop.sdk.source import SourceFilter
from vizydrop.fields import *


class TargetprocessBaseFilter(SourceFilter):
    opened = DateField(name="Opened", description="Date which an entity was opened", optional=True)
    started = DateField(name="Started", description="Date which work began on an entity", optional=True)
    closed = DateField(name="Closed", description="Date which an entity was closed", optional=True)

    def get_where_clause(self, return_formatted=True):
        where_pieces = []
        if self.opened:
            if isinstance(self.opened, date):
                # chances are we won't get an actual date object from Hermione, but this is here in case...
                where_pieces.append("CreateDate gte '{}'".format(self.opened.isoformat()))
            elif isinstance(self.opened, dict):
                if '_min' in self.opened.keys():
                    where_pieces.append("CreateDate gte '{}'".format(self.opened['_min']))
                if '_max' in self.opened.keys():
                    where_pieces.append("CreateDate lte '{}'".format(self.opened['_max']))
            elif isinstance(self.opened, str):
                where_pieces.append("CreateDate gte '{}'".format(self.opened))
        if self.closed:
            where_pieces.append("EndDate is not null")
            if isinstance(self.closed, date):
                where_pieces.append("EndDate gte '{}'".format(self.closed.isoformat()))
            elif isinstance(self.closed, dict):
                if '_min' in self.closed.keys():
                    where_pieces.append("EndDate gte '{}'".format(self.closed['_min']))
                if '_max' in self.closed.keys():
                    where_pieces.append("EndDate lte '{}'".format(self.closed['_max']))
            elif isinstance(self.closed, str):
                where_pieces.append("EndDate gte '{}'".format(self.closed))
        if self.started:
            where_pieces.append("StartDate is not null")
            if isinstance(self.started, date):
                where_pieces.append("StartDate gte '{}'".format(self.started.isoformat()))
            elif isinstance(self.started, dict):
                if '_min' in self.started.keys():
                    where_pieces.append("StartDate gte '{}'".format(self.started['_min']))
                if '_max' in self.started.keys():
                    where_pieces.append("StartDate lte '{}'".format(self.started['_max']))
            elif isinstance(self.started, str):
                where_pieces.append("StartDate gte '{}'".format(self.started))
        if return_formatted:
            return ' and '.join(['({})'.format(clause) for clause in where_pieces])
        else:
            return where_pieces


class TargetprocessAssignablesFilter(TargetprocessBaseFilter):
    def get_project_options(account, **kwargs):
        client = AsyncHTTPClient()
        uri = "{}/api/v1/Projects?take=100".format(account.tp_url)
        ret = []
        while uri is not None:
            req = account.get_request(uri)
            response = yield client.fetch(req)
            options = json.loads(response.body.decode('utf-8'))
            for option in options['Items']:
                ret.append({"value": option['Id'], "title": option['Name']})

            uri = options.get('Next', None)
            if uri is not None:
                # This escapes the filter, otherwise every request past the first will
                # return a 400
                uri = uri.replace(' ', '+')
        return ret

    def get_team_options(account, **kwargs):
        client = AsyncHTTPClient()
        uri = "{}/api/v1/Teams?take=100".format(account.tp_url)
        ret = []
        while uri is not None:
            req = account.get_request(uri)
            response = yield client.fetch(req)
            options = json.loads(response.body.decode('utf-8'))
            for option in options['Items']:
                ret.append({"value": option['Id'], "title": option['Name']})

            uri = options.get('Next', None)
            if uri is not None:
                # This escapes the filter, otherwise every request past the first will
                # return a 400
                uri = uri.replace(' ', '+')
        return ret

    projects = MultiListField(name="Project", description="Project IDs", optional=False,
                              get_options=get_project_options)
    teams = MultiListField(name="Team", description="Team IDs", optional=True, get_options=get_team_options)
    is_final = BooleanField(name="Is Final", description="Only include finished (closed) entities", optional=True)
    is_initial = BooleanField(name="Is Initial", description="Only include initial (backlog) entities", optional=True)

    def get_where_clause(self, return_formatted=True):
        where_pieces = super().get_where_clause(return_formatted=False)
        if self.projects:
            if self.projects.__len__() > 1:
                where_pieces.append("Project.Id in ({})".format(','.join(self.projects)))
            else:
                where_pieces.append("Project.Id eq {}".format(self.projects[0]))
        if self.teams:
            if self.teams.__len__() > 1:
                where_pieces.append("Team.Id in ({})".format(','.join(self.teams)))
            else:
                where_pieces.append("Team.Id eq {}".format(self.teams[0]))
        if self.is_final is True:
            where_pieces.append("EntityState.IsFinal eq 'true'")
        if self.is_initial is True:
            where_pieces.append("EntityState.IsInitial eq 'true'")
        if return_formatted:
            return ' and '.join(['({})'.format(clause) for clause in where_pieces])
        else:
            return where_pieces