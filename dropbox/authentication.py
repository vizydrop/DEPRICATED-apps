import json
from tornado import gen

import os
from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER
from tornado.httpclient import HTTPRequest, HTTPError, AsyncHTTPClient

from vizydrop.sdk.account import AppOAuthv2Account


class DropboxOAuth(AppOAuthv2Account):
    class Meta:
        identifier = 'oauth2'
        name = "OAuth v2 Authentication"
        description = "OAuth v2-based authentication and authorization for access to GitHub"

        client_id = os.environ.get('DROPBOX_CLIENT_ID', '')
        client_secret = os.environ.get('DROPBOX_CLIENT_SECRET', '')
        scope = None

        token_placement = AUTH_HEADER
        token_type = 'bearer'

        auth_uri = 'https://www.dropbox.com/1/oauth2/authorize?response_type=code&client_id={}'.format(
            os.environ.get('DROPBOX_CLIENT_SECRET', ''))
        token_uri = 'https://api.dropbox.com/1/oauth2/token'

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
            self.enabled = True

    @gen.coroutine
    def validate(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://api.dropbox.com/1/account/info")
            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except HTTPError as e:
            return False, e.response.reason

    @gen.coroutine
    def get_friendly_name(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://api.dropbox.com/1/account/info")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('display_name', 'Dropbox Account')
        except Exception:
            return "Dropbox Account"
