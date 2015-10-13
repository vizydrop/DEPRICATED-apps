from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class BoxDotComTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='box.boxdotcom')
        return app