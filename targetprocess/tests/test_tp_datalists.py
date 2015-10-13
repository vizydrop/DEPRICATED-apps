import json

from .test_tp_auth import VALID_ACCOUNT
from . import TargetprocessTpaTestCase


class TargetprocessDatalistTests(TargetprocessTpaTestCase):
    def test_boards_datalist(self):
        response = self.POST('/datalist?source=userstories&field=projects', data=json.dumps(VALID_ACCOUNT))

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIn('value', item.keys())
            self.assertIn('title', item.keys())
