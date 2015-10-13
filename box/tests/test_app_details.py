from . import BoxDotComTpaTestCase


class BoxDotComAppDetailsTests(BoxDotComTpaTestCase):
    def test_box_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)