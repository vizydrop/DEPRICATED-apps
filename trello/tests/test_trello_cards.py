from . import TrelloTpaTestCase
import json
from os import environ


class TrelloCardsSourceTest(TrelloTpaTestCase):
    def test_cards_source(self):
        payload = {"source": "cards", "account": {"auth": "token", "token": environ.get('TRELLO_VALID_TOKEN','')},
                   "filter": {"boards": ["4d5ea62fd76aa1136000000c"]}}
        response = self.POST('/', data=json.dumps(payload))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)