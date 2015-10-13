from . import GitHubTpaTestCase


class GitHubAppDetailsTests(GitHubTpaTestCase):
    def test_tp_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)
