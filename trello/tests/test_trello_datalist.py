from . import TrelloTpaTestCase
import json
from os import environ


class TrelloDatalistTests(TrelloTpaTestCase):
    def test_boards_datalist(self):
        payload = {"auth": "token", "token": environ.get('TRELLO_VALID_TOKEN','')}
        response = self.POST('/datalist?source=cards&field=boards', data=json.dumps(payload))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIn('value', item.keys())
            self.assertIn('title', item.keys())