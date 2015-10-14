import json
import re
from datetime import timedelta

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.locks import Condition
from tornado.log import app_log
from vizydrop.sdk.source import SourceFilter, SourceSchema, StreamingDataSource
from vizydrop.fields import *


# our maximum request time (in seconds)
MAXIMUM_REQ_TIME = 30


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
        if not spreadsheet:
            raise ValueError('spreadsheet ID required to gather list')
        client = AsyncHTTPClient()
        req = account.get_request(
            "https://spreadsheets.google.com/feeds/worksheets/{}/private/full".format(spreadsheet))
        response = yield client.fetch(req)
        response_object = json.loads(response.body.decode('utf-8'))
        ret = []
        id_ext = re.compile('gid=([A-Za-z0-9]+)')
        for item in response_object['feed']['entry']:
            title = item['title']['$t']
            csv_link = [link['href'] for link in item['link'] if link['type'] == 'text/csv']
            worksheet_gid = id_ext.search(csv_link[0]).groups()
            ret.append({"title": title, "value": worksheet_gid[0]})
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
        uri = "https://docs.google.com/spreadsheets/d/{}/export?format=csv&gid={}".format(
            source_filter.spreadsheet, source_filter.worksheet
        )

        app_log.info(
            "Start retrieval of worksheet {}/{} for {}".format(source_filter.spreadsheet, source_filter.worksheet,
                                                               account._id))

        lock = Condition()
        oauth_client = account.get_client()
        uri, headers, body = oauth_client.add_token(uri)
        req = HTTPRequest(uri, headers=headers, body=body, streaming_callback=lambda c: cls.write(c))

        client.fetch(req, callback=lambda r: lock.notify())
        yield lock.wait(timeout=timedelta(seconds=MAXIMUM_REQ_TIME))

        app_log.info(
            "Finished retrieving worksheet for {}".format(account._id))