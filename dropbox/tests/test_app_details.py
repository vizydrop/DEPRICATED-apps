from . import DropboxTpaTestCase


class DropboxAppDetailsTests(DropboxTpaTestCase):
    def test_dropbox_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)