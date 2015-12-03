from .authentication import GoogleSheetsOAuth
from .sheet import GoogleSheetSource
from vizydrop.sdk.application import Application


class GoogleSheets(Application):
    class Meta:
        version = "1.0"
        name = "Google Sheets"
        website = "https://docs.google.com/spreadsheets/"
        color = "#FFFFFF"
        description = "Create a new spreadsheet and edit with others at the same time -- from your computer, phone or" \
                      " tablet. Get stuff done with or without an internet connection."
        tags = ['spreadsheet', 'sheets', ]

        authentication = [GoogleSheetsOAuth, ]

        sources = [GoogleSheetSource, ]
