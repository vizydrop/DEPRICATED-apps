from datetime import timedelta
from urllib.request import urlopen, Request
import json
from tornado import gen, log

import os
from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER

from tornado.httpclient import HTTPRequest, HTTPError, AsyncHTTPClient

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

    def get_client(self):
        """
        Special hijack of our parent method so we can handle token expiration
        :return:
        """
        client = super(GoogleSheetsOAuth, self).get_client()
        if self.refresh_token:
            self._oauth_client.refresh_token = self.refresh_token
        if self.token_expiration and self.token_expiration < datetime.now():
            # we need to refresh our token
            log.app_log.info("Refreshing token for account {}".format(self._id))
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
            self._oauth_client.access_token = self.access_token
            self.token_expiration = datetime.now() + timedelta(seconds=int(response_data.get('expires_in')))
            log.app_log.info("Token refreshed successfully!")

        return client

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
        except HTTPError as e:
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
