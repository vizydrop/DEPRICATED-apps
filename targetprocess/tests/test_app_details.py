from . import TargetprocessTpaTestCase


class TargetprocessAppDetailsTests(TargetprocessTpaTestCase):
    def test_tp_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)
