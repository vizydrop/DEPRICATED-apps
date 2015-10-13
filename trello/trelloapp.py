from vizydrop.sdk.application import Application

from .authentication import TrelloOAuth, TrelloTokenAuth
from .cards import TrelloCardSource


class Trello(Application):
    class Meta:
        version = "1.0"
        name = "Trello"
        website = "http://www.trello.com/"
        color = "#0076C0"
        description = "Infinitely flexible. Incredibly easy to use. Great mobile apps. It's free. " \
                      "Trello keeps track of everything, from the big picture to the minute details."
        tags = ['kanban', 'project management', ]

        authentication = [TrelloOAuth, TrelloTokenAuth, ]

        sources = [TrelloCardSource, ]
