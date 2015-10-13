from vizydrop.sdk.application import Application

from .authentication import DropboxOAuth
from .files import DropboxFileSource


class Dropbox(Application):
    class Meta:
        version = "1.0"
        name = "Dropbox"
        website = "http://www.dropbox.com/"
        color = "#0076C0"
        description = "Good things happen when your stuff lives here. Dropbox keeps your files safe, synced, " \
                      "and easy to share."
        tags = ['cloud storage', 'files', ]

        authentication = [DropboxOAuth, ]

        sources = [DropboxFileSource, ]
