import json
import sys
from tornado import gen

from tornado.httpclient import AsyncHTTPClient, HTTPError

from tornado.log import app_log

from vizydrop.sdk.source import DataSource, SourceSchema, SourceFilter
from vizydrop.fields import *

RESPONSE_SIZE_LIMIT = 10  # MB


class TrelloCardSourceFilters(SourceFilter):
    def get_board_options(account, **kwargs):
        client = AsyncHTTPClient()
        req = account.get_request("https://api.trello.com/1/members/me/boards")
        response = yield client.fetch(req)
        options = json.loads(response.body.decode('utf-8'))
        ret = []
        for option in options:
            ret.append({"value": option['id'], "title": option['name']})
        return ret

    def get_list_options(account, boards, **kwargs):
        client = AsyncHTTPClient()
        ret = []
        if isinstance(boards, str):
            boards = boards.split(',')
        for board in boards:
            req = account.get_request("https://api.trello.com/1/boards/{}/lists".format(board))
            response = yield client.fetch(req)
            options = json.loads(response.body.decode('utf-8'))
            for option in options:
                ret.append({"value": option['id'], "title": option['name']})
        return ret

    boards = MultiListField(name="Board", description="Trello board", optional=False, get_options=get_board_options)
    lists = MultiListField(name="List", description="Board list", optional=True, get_options=get_list_options)


class TrelloCardSource(DataSource):
    class Meta:
        identifier = "cards"
        name = "Cards"
        tags = ["Kanban", "Cards", ]
        description = "List of cards"
        filter = TrelloCardSourceFilters

    class Schema(SourceSchema):
        id = IDField(description="Card ID")
        name = TextField(name="Name", description="Name of the card")
        board_name = TextField(name="Board Name", description="Name of the board")
        closed = BooleanField(name="Closed", description="Is the card closed?")
        desc = TextField(name="Description", description="Card Description")
        dateLastActivity = DateTimeField(name="Last Activity Date", description="Date/Time of last activity")
        pos = DecimalField(name="Position", description="Numeric representation of card's priority")
        due = DateTimeField(name="Due Date", description="Due date for card")
        labels = TextField(name="Labels", description="List of labels")
        list = TextField(name="List", description="Current list/state of the card")

    @classmethod
    @gen.coroutine
    def get_data(cls, account, source_filter, limit=100, skip=0):
        """
        Gathers card information from Trello
        GET https://api.trello.com/1/boards/[board_id]/cards
        """
        if not account:
            raise ValueError('cannot gather cards without an account')
        client = AsyncHTTPClient()

        app_log.info("Start retrieval of cards")

        cards = []
        for board in source_filter.boards:
            app_log.info("Retrieving board {}".format(board))

            try:
                resp = yield client.fetch(account.get_request("https://api.trello.com/1/boards/{}/name".format(board)))
            except HTTPError as err:
                return {"code": err.code, "reason": err.response.reason, "error": err.response.body.decode('utf-8')}
            else:
                board_name = json.loads(resp.body.decode('utf-8'))['_value']

            uri = "https://api.trello.com/1/boards/{}/cards".format(board)
            req = account.get_request(uri)
            try:
                response = yield client.fetch(req)
            except HTTPError as e:
                return {
                    "code": e.code,
                    "reason": e.response.reason,
                    "error": e.response.body.decode('utf-8')
                }

            if response.code != 200:
                return {
                    "code": response.code,
                    "reason": response.reason,
                    "error": response.error
                }
            data = response.body.decode('utf-8')
            resp_obj = json.loads(data)

            for obj in resp_obj:
                obj['board_name'] = board_name

                if hasattr(source_filter,
                           'lists') and source_filter.lists is not None and source_filter.lists.__len__() > 0:
                    if obj['idList'] in source_filter.lists:
                        cards.append(obj)
                else:
                    cards.append(obj)
            app_log.info("Board {} retrieved {} cards".format(board, cards.__len__()))

            # check our response size
            if sys.getsizeof(cards) > RESPONSE_SIZE_LIMIT * 1000000:
                app_log.warn("Request for {} exceeds size limit".format(account._id))
                raise HTTPError(413)

        list_ids = set([el['idList'] for el in cards])
        boards = set([el['idBoard'] for el in cards])
        list_name_map = {}
        # grab our list names
        app_log.info("Starting resolution of lists")
        for board in boards:
            app_log.info("Resolving list names for {}".format(board))
            uri = "https://api.trello.com/1/boards/{}/lists".format(board)
            req = account.get_request(uri)
            try:
                response = yield client.fetch(req)
            except HTTPError as e:
                return {
                    "code": e.code,
                    "reason": e.response.reason,
                    "error": e.response.body.decode('utf-8')
                }
            lists = json.loads(response.body.decode('utf-8'))
            for list in lists:
                if list['id'] not in list_ids:
                    continue
                list_name_map[list['id']] = list['name']
            app_log.info("Board {} resolution yielded {} lists".format(board, lists.__len__()))

        for card in cards:
            card['list'] = list_name_map[card['idList']]
            card['labels'] = ','.join(label['name'] for label in card['labels'])

        reply_data = cls.format_data_to_schema(cards)

        app_log.info("Source complete, grabbed {} cards".format(cards.__len__()))
        return json.dumps(reply_data)
