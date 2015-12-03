from vizydrop.sdk.application import Application

from .authentication import MicrosoftLiveAccount
from .files import OneDriveFileSource

class OneDrive(Application):
    class Meta:
        version = "1.0"
        name = "OneDrive"
        website = "http://www.onedrive.com/"
        color = "#FFFFFF"
        description = "OneDrive is the one place for everything in your work and personal life. It gives you free " \
                      "online storage for all your personal files so that you can get to them from anywhere."
        tags = ['cloud storage', 'files', ]

        authentication = [MicrosoftLiveAccount, ]

        sources = [OneDriveFileSource, ]
