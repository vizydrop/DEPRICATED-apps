import json

from . import TargetprocessTpaTestCase
from os import environ

VALID_ACCOUNT = {"auth": "basic", "tp_url": environ.get('TP_URL',''), "username": environ.get('TP_USER',''),
                 "password": environ.get('TP_PASS','')}


class TargetprocessAuthTests(TargetprocessTpaTestCase):
    def test_validate_account(self):
        payload = {"id": "basic", "fields": VALID_ACCOUNT}
        response = self.POST('/validate', data=json.dumps(payload))

        self.assertHttpOk(response)

        response_data = self.json_resp(response)
        self.assertIsInstance(response_data, dict)
        self.assertIn('name', response_data)
