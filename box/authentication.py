import json
from datetime import datetime, timedelta
from urllib.request import urlopen, Request, HTTPError
from tornado import gen, log

import os

from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httpclient import HTTPError as AsyncHTTPError

from vizydrop.sdk.account import AppOAuthv2Account
from vizydrop.fields import TextField, DateTimeField


class BoxOAuth(AppOAuthv2Account):
    token_expiration = DateTimeField(name="OAuth Token Expiration")
    refresh_token = TextField(name="OAuth Refresh Token")

    class Meta:
        identifier = 'oauth2'
        name = "OAuth v2 Authentication"
        description = "OAuth v2-based authentication and authorization for access to Box.com"

        client_id = os.environ.get('BOX_CLIENT_ID', '')
        client_secret = os.environ.get('BOX_CLIENT_SECRET', '')
        scope = None

        token_placement = AUTH_HEADER
        token_type = 'bearer'

        auth_uri = 'https://app.box.com/api/oauth2/authorize'
        token_uri = 'https://app.box.com/api/oauth2/token'

    def get_request(self, url, **kwargs):
        client = self.get_client()
        uri, headers, body = client.add_token(url, **kwargs)
        return HTTPRequest(uri, headers=headers, body=body)

    def finish_setup(self, provider_response):
        response = json.loads(provider_response.body.decode('utf-8'))
        token = response.get('access_token', None)
        if not token:
            raise ValueError(response.get('error_description', ['An unknown error occurred'])[0])
        else:
            self.access_token = token
            self.refresh_token = response.get('refresh_token')
            self.token_expiration = datetime.now() + timedelta(seconds=int(response.get('expires_in')))
            self.enabled = True

    @gen.coroutine
    def validate(self):
        try:
            yield self.do_token_refresh()
            client = AsyncHTTPClient()
            req = self.get_request("https://api.box.com/2.0/users/me")
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
            req = self.get_request("https://api.box.com/2.0/users/me")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('name', 'Box.com Account')
        except Exception:
            return "Box.com Account"
