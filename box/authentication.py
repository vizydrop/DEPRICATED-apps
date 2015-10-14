import json
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from tornado import gen, log

import os

from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER

from tornado.httpclient import HTTPError, AsyncHTTPClient, HTTPRequest

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

    def get_client(self):
        """
        Special hijack of our parent method so we can handle token expiration
        :return:
        """
        client = super(BoxOAuth, self).get_client()
        if self.refresh_token:
            self._oauth_client.refresh_token = self.refresh_token
        if self.token_expiration and self.token_expiration < datetime.now():
            # we need to refresh our token
            log.app_log.info("Refreshing token for account {}".format(self._id))
            try:
                uri, headers, body = self._oauth_client.prepare_refresh_token_request(self.Meta.token_uri,
                                                                                      client_id=self.Meta.client_id,
                                                                                      client_secret=self.Meta.client_secret,
                                                                                      refresh_token=self.refresh_token)

                token_request = Request(uri, data=body.encode('utf-8'), headers=headers, method='POST')
                # this needs to be blocking to avoid a race condition
                request = urlopen(token_request)
                response = request.read().decode('utf-8')

                response_data = json.loads(response)
                self.access_token = response_data.get('access_token')
                self.refresh_token = response_data.get('refresh_token', self.refresh_token)
                self.token_expiration = datetime.now() + timedelta(seconds=int(response_data.get('expires_in')))
                self._oauth_client.refresh_token = self.refresh_token
                self._oauth_client.access_token = self.access_token
                log.app_log.info("Token refreshed successfully!")
            except HTTPError as e:
                log.app_log.error("Error refreshing token {} ({})".format(self._id, e.response.body.decode('utf-8')))
                raise e

        return client

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
            client = AsyncHTTPClient()
            req = self.get_request("https://api.box.com/2.0/users/me")
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
            req = self.get_request("https://api.box.com/2.0/users/me")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('name', 'Box.com Account')
        except Exception:
            return "Box.com Account"
