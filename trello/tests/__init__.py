from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class TrelloTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='trello.trelloapp')
        return app