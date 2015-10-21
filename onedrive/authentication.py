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

    def get_client(self):
        """
        Special hijack of our parent method so we can handle token expiration
        :return:
        """
        client = super(MicrosoftLiveAccount, self).get_client()
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
                self.token_expiration = datetime.now() + timedelta(seconds=int(response_data.get('expires_in')))
            except HTTPError as e:
                log.app_log.error("Error refreshing token {} ({})".format(self._id, e.readlines()))
                raise e

        return client

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
