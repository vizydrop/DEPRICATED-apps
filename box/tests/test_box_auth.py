from . import BoxDotComTpaTestCase


class DropboxAuthTests(BoxDotComTpaTestCase):
    def test_dropbox_oauth_start(self):
        response = self.GET('/oauth2?callback_uri=http%3A%2F%2F127.0.0.1%3A3000')

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, dict)
        self.assertIn('redirect_uri', json_resp.keys())
