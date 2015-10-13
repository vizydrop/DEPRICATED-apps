from . import OneDriveTpaTestCase


class OneDriveAppDetailsTests(OneDriveTpaTestCase):
    def test_tp_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)
