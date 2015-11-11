from datetime import timedelta, datetime
from urllib.request import urlopen, Request, HTTPError
import json
from tornado import gen, log

import os
from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER

from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.httpclient import HTTPError as AsyncHTTPError

from vizydrop.fields import *
from vizydrop.sdk.account import AppOAuthv2Account


class GoogleSheetsOAuth(AppOAuthv2Account):
    token_expiration = DateTimeField(name="OAuth Token Expiration")
    refresh_token = TextField(name="OAuth Refresh Token")

    class Meta:
        identifier = 'oauth2'
        name = "OAuth v2 Authentication"
        description = "OAuth v2-based authentication and authorization for access to Google Drive"

        client_id = os.environ.get('GSHEETS_CLIENT_ID', '')
        client_secret = os.environ.get('GSHEETS_CLIENT_SECRET', '')
        scope = 'https://spreadsheets.google.com/feeds https://docs.google.com/feeds https://www.googleapis.com/auth/userinfo.profile'

        token_placement = AUTH_HEADER
        token_type = 'Bearer'

        auth_uri = 'https://accounts.google.com/o/oauth2/auth'
        token_uri = 'https://accounts.google.com/o/oauth2/token'

        additional_request_parameters = {"access_type": "offline", "approval_prompt": "force"}

    def get_request(self, url, **kwargs):
        client = self.get_client()
        url = ('&' if '?' in url else '?').join([url, 'alt=json'])
        uri, headers, body = client.add_token(url, **kwargs)
        return HTTPRequest(uri, headers=headers, body=body)

    def finish_setup(self, provider_response):
        response = json.loads(provider_response.body.decode('utf-8'))
        token = response.get('access_token', None)
        if not token:
            # TODO, this should be more gracefully dealt with
            raise NotImplementedError
        else:
            self.access_token = token
            self.refresh_token = response.get('refresh_token')
            self.token_expiration = datetime.now() + timedelta(seconds=int(response.get('expires_in')))
            self.enabled = True

    @gen.coroutine
    def validate(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://spreadsheets.google.com/feeds/spreadsheets/private/full")
            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except AsyncHTTPError as e:
            return False, e.response.reason

    @gen.coroutine
    def get_friendly_name(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://www.googleapis.com/oauth2/v1/userinfo?alt=json")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('email', resp_data.get('name', 'Google Account'))
        except Exception as e:
            log.app_log.error(e)
        return 'Google Account'
