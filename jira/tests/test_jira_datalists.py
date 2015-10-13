import json

from . import JiraTpaTestCase
from .test_jira_auth import VALID_ACCOUNT


class JiraDatalistTests(JiraTpaTestCase):
    def test_jira_projects_datalist(self):
        response = self.POST('/datalist?source=issues&field=projects', data=json.dumps(VALID_ACCOUNT))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIn('value', item.keys())
            self.assertIn('title', item.keys())

    def test_jira_issue_types_datalist(self):
        response = self.POST('/datalist?source=issues&field=issue_types', data=json.dumps(VALID_ACCOUNT))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIn('value', item.keys())
            self.assertIn('title', item.keys())

    def test_jira_states_datalist(self):
        response = self.POST('/datalist?source=issues&field=states&projects=VZDRP', data=json.dumps(VALID_ACCOUNT))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIn('value', item.keys())
            self.assertIn('title', item.keys())