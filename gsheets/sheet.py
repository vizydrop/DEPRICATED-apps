import json
from tornado import gen

from tornado.httpclient import AsyncHTTPClient, HTTPError

from tornado.log import app_log

from vizydrop.sdk.source import SourceFilter, SourceSchema, StreamingDataSource
from vizydrop.fields import *


class GoogleSheetSourceFilter(SourceFilter):
    def get_spreadsheet_list(account, **kwargs):
        client = AsyncHTTPClient()
        req = account.get_request("https://spreadsheets.google.com/feeds/spreadsheets/private/full")
        response = yield client.fetch(req)
        response_object = json.loads(response.body.decode('utf-8'))
        id_ext = re.compile('([A-Za-z0-9\-_]{18,})')
        ret = [{"value": id_ext.search(option['id']['$t']).groups()[0], "title": option['title']['$t']}
               for option in response_object['feed']['entry']]
        return ret

    def get_worksheet_list(account, spreadsheet, **kwargs):
        request = kwargs.get('request')
        if not spreadsheet:
            raise ValueError('spreadsheet ID required to gather list')
        client = AsyncHTTPClient()
        req = account.get_request(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full".format(spreadsheet))
        response = yield client.fetch(req)
        response_object = json.loads(response.body.decode('utf-8'))
        id_ext = re.compile('/([\w\d]+)$')
        ret = [{"value": id_ext.search(option['id']['$t']).groups()[0], "title": option['title']['$t']}
               for option in response_object['feed']['entry']]
        return ret

    spreadsheet = TextField(description="Google Sheets spreadsheet ID", optional=False,
                            get_options=get_spreadsheet_list, name="Spreadsheet")
    worksheet = TextField(description="Google Sheets worksheet ID", optional=False, get_options=get_worksheet_list,
                          name="Worksheet")


class GoogleSheetSource(StreamingDataSource):
    class Meta:
        identifier = "sheet"
        name = "Sheet"
        tags = ["spreadsheet", "google sheets", ]
        description = "Data from a Google Sheet"
        filter = GoogleSheetSourceFilter

    class Schema(SourceSchema):
        pass

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        """
        Gathers card information from Google Sheets
        GET https://spreadsheets.google.com/feeds/list/[spreadsheet]/[worksheet]/private/full
        """
        if not account or not account.enabled:
            raise ValueError('cannot gather information without an account')
        client = AsyncHTTPClient()

        if source_filter.spreadsheet is None:
            raise ValueError('required parameter spreadsheet missing')
        if source_filter.worksheet is None:
            raise ValueError('required parameter worksheet missing')
        uri = "https://spreadsheets.google.com/feeds/list/{}/{}/private/full".format(source_filter.spreadsheet,
                                                                                     source_filter.worksheet)

        app_log.info(
            "Start retrieval of worksheet {}/{} for {}".format(source_filter.spreadsheet, source_filter.worksheet,
                                                               account._id))

        req = account.get_request(uri)
        response = yield client.fetch(req)

        if response.code != 200:
            raise HTTPError(response.code, message=response.reason, response=response)

        data = response.body.decode('utf-8')
        resp_obj = json.loads(data)
        sheet_lines = resp_obj['feed']['entry']

        cls.write('[')
        lines = 0
        for line in sheet_lines:
            this_line = {}
            for key in [key for key in line.keys() if key.startswith('gsx$')]:
                this_line[key[4:]] = line[key]['$t']
            if lines > 0:
                cls.write(',')
            cls.write(json.dumps(this_line))
            lines += 1

        cls.write(']')
        app_log.info(
            "Finished retrieving worksheet for {}".format(account._id))
