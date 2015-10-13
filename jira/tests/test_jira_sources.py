from .test_jira_auth import VALID_ACCOUNT
from . import JiraTpaTestCase
from datetime import date, datetime
from dateutil.parser import parse as date_parse
import json


class JiraSourceTests(JiraTpaTestCase):
    def test_issues_source(self):
        payload = {"source": "issues", "account": VALID_ACCOUNT, "filter": {"projects": ["VZDRP"]}}
        response = self.POST('/', data=json.dumps(payload))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

    def test_issues_source_with_date_filter(self):
        payload = {"source": "issues", "account": VALID_ACCOUNT, "filter": {"projects": ["VZDRP"],
                                                                            "created": {
                                                                                "_min": date(2015, 4, 1).isoformat(),
                                                                                "_max": date(2015, 4, 30).isoformat()
                                                                            }}}
        response = self.POST('/', data=json.dumps(payload))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIsNotNone(item['created'])
            create_date = date_parse(item['created'])
            self.assertLess(create_date, datetime(2015, 4, 30, tzinfo=create_date.tzinfo))
            self.assertGreater(create_date, datetime(2015, 4, 1, tzinfo=create_date.tzinfo))
