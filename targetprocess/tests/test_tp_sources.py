from . import TargetprocessTpaTestCase
from .test_tp_auth import VALID_ACCOUNT
from datetime import date, datetime
from dateutil.parser import parse as date_parse
import json


class TargetprocessSourceTests(TargetprocessTpaTestCase):
    def get_collection(self, collection, **kwargs):
        filters = {"projects": [13]}
        filters.update(kwargs)

        return self.POST('/', data=json.dumps({"source": collection, "account": VALID_ACCOUNT, "filter": filters}))

    def run_tests_with(self, collection):
        response = self.get_collection(collection)

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        return json_resp

    def test_get_requests(self):
        self.run_tests_with('requests')

    def test_get_userstories(self):
        response = self.run_tests_with('userstories')
        # be sure our shims work
        self.assertIn('Feature', response[0].keys())

    def test_get_bugs(self):
        response = self.run_tests_with('bugs')

        # be sure our shims work
        self.assertIn('Severity', response[0].keys())
        self.assertIn('UserStory', response[0].keys())
        self.assertIn('Feature', response[0].keys())

    def test_get_tasks(self):
        self.run_tests_with('tasks')

    def test_get_features(self):
        self.run_tests_with('features')

    def test_get_epics(self):
        self.run_tests_with('epics')

    def test_get_projects(self):
        self.run_tests_with('project')

    def test_get_programs(self):
        self.run_tests_with('program')

    def test_get_assignables(self):
        response = self.run_tests_with('assignables')
        # be sure our EntityType shim works
        self.assertIn('EntityType', response[0].keys())

    def test_get_with_date_opened_filter(self):
        date_filter = {
            '_min': date(2015, 4, 1).isoformat(),
            '_max': date(2015, 4, 25).isoformat()
        }
        response = self.get_collection('userstories', opened=date_filter)

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIsNotNone(item['CreateDate'])
            create_date = date_parse(item['CreateDate'])
            self.assertLess(create_date, datetime(2015, 4, 25, tzinfo=create_date.tzinfo))
            self.assertGreater(create_date, datetime(2015, 4, 1, tzinfo=create_date.tzinfo))

    def test_get_with_date_closed_filter(self):
        date_filter = {
            '_min': date(2015, 4, 1).isoformat(),
            '_max': date(2015, 4, 25).isoformat()
        }
        response = self.get_collection('userstories', closed=date_filter)

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIsNotNone(item['EndDate'])
            end_date = date_parse(item['EndDate'])
            self.assertLess(end_date, datetime(2015, 4, 25, tzinfo=end_date.tzinfo))
            self.assertGreater(end_date, datetime(2015, 4, 1, tzinfo=end_date.tzinfo))

    def test_get_with_date_started_filter(self):
        date_filter = {
            '_min': date(2015, 4, 1).isoformat(),
            '_max': date(2015, 4, 25).isoformat()
        }
        response = self.get_collection('userstories', started=date_filter)

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, list)

        for item in json_resp:
            self.assertIsNotNone(item['StartDate'])
            start_date = date_parse(item['StartDate'])
            self.assertLess(start_date, datetime(2015, 4, 25, tzinfo=start_date.tzinfo))
            self.assertGreater(start_date, datetime(2015, 4, 1, tzinfo=start_date.tzinfo))

    def test_team_list_not_broken(self):
        # this test is here only because of uncertainty around the underlying API
        assignables = self.run_tests_with('assignables')
        self.assertIn('Teams', assignables[0].keys())
