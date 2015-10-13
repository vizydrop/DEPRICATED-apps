from . import TrelloTpaTestCase
import json
from os import environ


class TrelloAuthTests(TrelloTpaTestCase):
    def test_validate_token(self):
        payload = {"id": "token", "fields": {"token": environ.get('TRELLO_VALID_TOKEN','')}}
        response = self.POST('/validate', data=json.dumps(payload))

        self.assertHttpOk(response)

        response_data = self.json_resp(response)
        self.assertIsInstance(response_data, dict)
        self.assertIn('name', response_data)

    def test_validate_bad_token(self):
        payload = {"id": "token", "fields": {"token": "BADSTUFFZ"}}
        response = self.POST('/validate', data=json.dumps(payload))

        self.assertEqual(response.code, 401)

    def test_trello_oauth_start(self):
        response = self.GET('/oauth1?callback_uri=http%3A%2F%2F127.0.0.1%3A8888')

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, dict)
        self.assertIn('redirect_uri', json_resp.keys())
