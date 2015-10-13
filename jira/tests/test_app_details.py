from . import JiraTpaTestCase


class JiraAppDetailsTests(JiraTpaTestCase):
    def test_tp_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)
