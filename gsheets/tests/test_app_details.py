from . import GoogleSheetsTpaTestCase


class GoogleSheetsAppDetailsTests(GoogleSheetsTpaTestCase):
    def test_tp_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)
