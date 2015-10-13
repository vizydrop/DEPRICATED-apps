from . import GitHubTpaTestCase


class GitHubAuthTests(GitHubTpaTestCase):
    def test_github_oauth_start(self):
        response = self.GET('/oauth2?callback_uri=http%3A%2F%2F127.0.0.1%3A8888')

        self.assertHttpOk(response)
        json_resp = self.json_resp(response)
        self.assertIsInstance(json_resp, dict)
        self.assertIn('redirect_uri', json_resp.keys())
