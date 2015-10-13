from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class DropboxTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='dropbox.dropbox')
        return app