from . import JiraTpaTestCase
import json
from os import environ

VALID_ACCOUNT = {"auth": "basic", "jira_url": environ.get('JIRA_URL',''), "username": environ.get('JIRA_USER', ''),
                 "password": environ.get('JIRA_PASS', '')}

class TestJIRABasicAuth(JiraTpaTestCase):
    def test_validate_account(self):
        payload = {"id": "basic", "fields": VALID_ACCOUNT}
        response = self.POST('/validate', data=json.dumps(payload))

        self.assertHttpOk(response)

        response_data = self.json_resp(response)
        self.assertIsInstance(response_data, dict)
        self.assertIn('name', response_data)
