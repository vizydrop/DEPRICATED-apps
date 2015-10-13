from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class GoogleSheetsTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='gsheets.google_sheets')
        return app