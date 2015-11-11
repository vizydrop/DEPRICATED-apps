import json
import os
from urllib.request import urlopen, Request, HTTPError
from datetime import timedelta, datetime

from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.httpclient import HTTPError as AsyncHTTPError
from tornado import gen, log

from vizydrop.fields import *
from vizydrop.sdk.account import AppOAuthv2Account


class MicrosoftLiveAccount(AppOAuthv2Account):
    token_expiration = DateTimeField(name="OAuth Token Expiration")
    refresh_token = TextField(name="OAuth Refresh Token")

    class Meta:
        identifier = 'oauth2'
        name = "OAuth v2 Authentication"
        description = "OAuth v2-based authentication and authorization for access to Microsoft Live services"

        client_id = os.environ.get('ONEDRIVE_CLIENT_ID', '')
        client_secret = os.environ.get('ONEDRIVE_CLIENT_SECRET', '')
        scope = 'wl.basic wl.offline_access onedrive.readonly'

        token_placement = AUTH_HEADER
        token_type = 'bearer'

        auth_uri = 'https://login.live.com/oauth20_authorize.srf'
        token_uri = 'https://login.live.com/oauth20_token.srf'

    def get_request(self, url, **kwargs):
        client = self.get_client()
        uri, headers, body = client.add_token(url, **kwargs)
        return HTTPRequest(uri, headers=headers, body=body)

    def finish_setup(self, provider_response):
        response_body = provider_response.body.decode('utf-8')
        response = json.loads(response_body)
        token = response.get('access_token', None)
        if token is None:
            raise ValueError(response.get('error_description', ['An unknown error occurred'])[0])
        else:
            self.access_token = token
            self.refresh_token = response.get('refresh_token')
            self.token_expiration = datetime.now() + timedelta(seconds=int(response.get('expires_in')))
            self.enabled = True

    @gen.coroutine
    def validate(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://apis.live.net/v5.0/me")
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
            req = self.get_request("https://apis.live.net/v5.0/me")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('name', 'OneDrive Account')
        except Exception:
            return "OneDrive Account"
