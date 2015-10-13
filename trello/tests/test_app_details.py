from . import TrelloTpaTestCase
from trello.trelloapp import Trello
from trello.authentication import *


class TrelloAppDetailsTests(TrelloTpaTestCase):
    def test_token_auth_type(self):
        auth = Trello.get_auth('token')
        self.assertIs(auth, TrelloTokenAuth)

    def test_oauth_auth_type(self):
        auth = Trello.get_auth('oauth')
        self.assertIs(auth, TrelloOAuth)

    def test_trello_info(self):
        response = self.GET('/')

        self.assertHttpOk(response)
        self.assertInfoResponseValid(response)