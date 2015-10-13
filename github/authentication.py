from urllib.parse import parse_qs
import json
import os
from oauthlib.oauth2.rfc6749.clients.base import AUTH_HEADER
from tornado.httpclient import HTTPRequest, HTTPError, AsyncHTTPClient

from tornado import gen

from vizydrop.sdk.account import AppOAuthv2Account
from . import __version__


class GitHubOAuth(AppOAuthv2Account):
    class Meta:
        identifier = 'oauth2'
        name = "OAuth v2 Authentication"
        description = "OAuth v2-based authentication and authorization for access to GitHub"

        client_id = os.environ.get('GITHUB_CLIENT_ID', '')
        client_secret = os.environ.get('GITHUB_CLIENT_SECRET', '')
        scope = 'repo'

        token_placement = AUTH_HEADER
        token_type = 'bearer'

        auth_uri = 'https://github.com/login/oauth/authorize'
        token_uri = 'https://github.com/login/oauth/access_token'

        additional_request_parameters = {"access_type": "offline", "approval_prompt": "force"}

    def get_request(self, url, **kwargs):
        client = self.get_client()
        headers = kwargs.pop('headers', {})
        # GitHub requires a user-agent be specified for all API requests
        headers['User-Agent'] = 'Vizydrop-Hermione/AppsGallery github/{}'.format(__version__)
        uri, headers, body = client.add_token(url, headers=headers, **kwargs)
        return HTTPRequest(uri, headers=headers, body=body)

    def finish_setup(self, provider_response):
        response_body = provider_response.body.decode('utf-8')
        response = parse_qs(response_body)
        token = response.get('access_token', None)
        if token is None:
            raise ValueError(response.get('error_description', ['An unknown error occurred'])[0])
        else:
            self.access_token = token[0]
            self.enabled = True

    @gen.coroutine
    def validate(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://api.github.com/user")
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
            req = self.get_request("https://api.github.com/user")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('login', 'GitHub Account')
        except Exception:
            return "GitHub Account"
