from vizydrop.tests import AppTestCase
from vizydrop.tpa import VizydropTPAHost


class JiraTpaTestCase(AppTestCase):
    def get_app(self):
        app = VizydropTPAHost(app_module='jira.atlassian_jira')
        return app