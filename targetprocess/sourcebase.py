from datetime import datetime
import json
import sys
from tornado import gen
from urllib.parse import urlencode

from dateutil.parser import parse as parse_date
import re
from tornado.httpclient import AsyncHTTPClient

from tornado.log import app_log

from targetprocess.filter import TargetprocessAssignablesFilter
from vizydrop.fields import NumberField, TextField, DateField, DecimalField, IDField
from vizydrop.sdk.source import StreamingDataSource, SourceSchema


class TargetprocessGeneral(StreamingDataSource):
    class Meta:
        tp_api_call = "Generals"

    class Schema(SourceSchema):
        Id = IDField(name="ID", description="Entity ID", force_int=True)
        Name = TextField(name="Name", description="Entity name or title")
        StartDate = DateField(name="Start Date",
                              description="Start date for time-boxed entities such as Iteration, Project, Release")
        EndDate = DateField(name="End Date",
                            description="End date for time-boxed entities such as Iteration, Project, Release")
        CreateDate = DateField(name="Create Date", description="Entity creation date")
        Tags = TextField(name="Tags", description="List of tags")
        Project = TextField(name="Project", description="Project where entity is found", response_loc="Project-Name")

    @classmethod
    def get_api_includes(cls):
        """
        Gathers the TP API's include fields based on our source schema
        :return:
        """
        includes = []
        for name, field in cls.Schema.get_all_fields():
            if field.response_location is not None:
                # convert our response location pieces delimited by a hyphen
                # to TP's API x[y[z]] format for include
                pieces = field.response_location.split('-')
                include = '['.join(pieces) + ''.join([']' for n in range(pieces.__len__() - 1)])
                includes.append(include)
            else:
                # if we have no response location, our name is the location
                includes.append(name)
        return '[{}]'.format(','.join(includes))

    @classmethod
    def _get_value_from_location(cls, item, location):
        """
        Adds some extra spice to this function to deal with TargetProcess' collections
        :param item: dict to search through
        :param location: location to get the value from, nested dictionaries can be separated by a hyphen (-)
        :return: value
        """
        if location is None or item is None:
            return None
        if 'Items' in item.keys():
            # handle our inner collections
            return ','.join([cls._get_value_from_location(i, location) for i in item['Items']])
        return super(TargetprocessGeneral, cls)._get_value_from_location(item, location)

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        try:
            # first try the filter specified in our Meta-class
            source_filter = cls.Meta.filter(source_filter)
        except AttributeError:
            # and fallback to our base assignables filter if that fails
            source_filter = TargetprocessAssignablesFilter(source_filter)

        where_clause = source_filter.get_where_clause()

        client = AsyncHTTPClient()

        app_log.info("Start retrieval of {} for {}".format(cls.Meta.tp_api_call, account._id))

        uri = "{}/api/v1/{}".format(account.tp_url, cls.Meta.tp_api_call)
        query_params = {}
        if where_clause != "":
            query_params['where'] = where_clause
        if skip > 0:
            query_params['skip'] = skip
        page_limit = limit if limit is not None else 1000  # TP API's maximum page size
        query_params['take'] = page_limit
        query_params['include'] = cls.get_api_includes()

        uri = '?'.join([uri, urlencode(query_params)])
        date_re = re.compile(r'\((\d+)([\+\-])(\d+)\)')
        # hold our counts and track the amount of data we've already streamed
        # (for maximum response sizes)
        item_count = 0
        response_size = 1

        # open our list
        cls.write('[')

        while uri is not None:
            req = account.get_request(uri)

            response = yield client.fetch(req)

            page_data = response.body.decode('utf-8')
            resp_obj = json.loads(page_data)

            app_log.info("Start retrieval; first page...")
            for item in resp_obj['Items']:
                # convert our dates to something understandable
                # TP dates come in as something like \/Date(1429890000000-0500)\/
                # we put them out in 8601
                for name, field in cls.Schema.get_all_fields():
                    if not isinstance(field, DateField):
                        continue
                    val = item[name]
                    if val is not None and isinstance(val, str):
                        search = date_re.search(val)
                        if search is None:
                            continue
                        pieces = search.groups()
                        timestamp = int(int(pieces[0]) / 1000)
                        val = parse_date(datetime.fromtimestamp(timestamp).isoformat()
                                         + ''.join(pieces[1:])).strftime('%Y-%m-%dT%H:%M:%S%z')
                    item[name] = val
                formatted = cls.format_data_to_schema(item)
                response_size += sys.getsizeof(formatted)
                if item_count > 0:
                    cls.write(',')
                cls.write(json.dumps(formatted))
                item_count += 1

            uri = resp_obj.get('Next', None)
            if uri is not None:
                app_log.info(
                    "Next page for {}, retrieved {} thus far".format(account._id, item_count))
                # This escapes the filter, otherwise every request past the first will
                # return a 400
                uri = uri.replace(' ', '+')
            else:
                app_log.info("At end of response for {}".format(account._id))
        # close our array
        cls.write(']')
        # finish
        app_log.info(
            "Finished retrieval of {} {} for {}".format(item_count, cls.Meta.tp_api_call, account._id))


class TargetprocessAssignable(TargetprocessGeneral):
    class Schema(TargetprocessGeneral.Schema):
        Effort = DecimalField(name="Effort", description="Total efforts for assignable")
        EffortCompleted = DecimalField(name="Effort Completed", description="Effort spent on assignment")
        EffortToDo = DecimalField(name="Effort ToDo", description="Effort required to complete assignment")
        Progress = DecimalField(name="Progress", description="Percent done for assignable")
        TimeSpent = DecimalField(name="Time Spent", description="Total time spent on assignment")
        TimeRemain = DecimalField(name="Time Remain",
                                  description="Total time remaining to complete assignment for Role")
        PlannedStartDate = DateField(name="Planned Start Date",
                                     description="Planned Start date for time-boxed entities such as Iteration, Project, Release")
        PlannedEndDate = DateField(name="Planned End Date",
                                   description="Planned End date for time-boxed entities such as Iteration, Project, Release")
        Assignments = TextField(name="Assignment", description="User assigned to this item",
                                response_loc="Assignments-GeneralUser-LastName")
        LeadTime = NumberField(name="Lead Time",
                               description="Number of days between assignable create date and end date")
        CycleTime = NumberField(name="Cycle Time",
                                description="Number of days between assignable start date and end date")
        ForecastEndDate = DateField(name="Forecast End Date", description="End date predicted on current progress")
        Iteration = TextField(name="Iteration", description="Assignable entity can be assigned to Iteration",
                              response_loc="Iteration-Name")
        TeamIteration = TextField(name="Team Iteration",
                                  description="Assignable entity can be assigned to TeamIteration",
                                  response_loc="TeamIteration-Name")
        Release = TextField(name="Release",
                            description="Assignable entity can be assigned to Release or can be in project Backlog (Release is not defined in this case)",
                            response_loc="Release-Name")
        EntityState = TextField(name="Entity State", description="State of Assignable",
                                response_loc="EntityState-Name")
        Priority = TextField(name="Priority", description="Priority of Assignable", response_loc="Priority-Name")
        Teams = TextField(name="Teams", description="Assigned Team(s)", response_loc="AssignedTeams-Team-Name")