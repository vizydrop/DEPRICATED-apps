from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class OneDriveTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='onedrive.msonedrive')
        return app