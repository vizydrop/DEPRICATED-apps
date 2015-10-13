from vizydrop.sdk.application import Application

from .authentication import BoxOAuth
from .files import BoxFileSource


class Box(Application):
    class Meta:
        version = "1.0"
        name = "Box.com"
        website = "http://www.box.com/"
        color = "#0076C0"
        description = "Box offers secure content management and collaboration for individuals, teams and businesses, " \
                      "enabling secure file sharing and access to your files online."
        tags = ['cloud storage', 'files', ]

        authentication = [BoxOAuth, ]

        sources = [BoxFileSource, ]
