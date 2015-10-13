from tornado import gen
import json

from tornado.httpclient import HTTPRequest, HTTPError, AsyncHTTPClient
import os

from vizydrop.sdk.account import Account, AppOAuthv1Account
from vizydrop.fields import TextField, LinkField


class TrelloOAuth(AppOAuthv1Account):
    class Meta:
        name = "OAuth Authentication"
        description = "OAuth-based authentication and authorization for access to Trello"
        client_key = os.environ.get('TRELLO_CLIENT_ID', '')
        client_secret = os.environ.get('TRELLO_CLIENT_SECRET', '')
        request_token_uri = "https://trello.com/1/OAuthGetRequestToken"
        access_token_uri = "https://trello.com/1/OAuthGetAccessToken"
        authorize_token_uri = "https://trello.com/1/OAuthAuthorizeToken"

    def get_authorize_uri(self, token):
        return self.Meta.authorize_token_uri + "?name=Vizydrop&oauth_token=" + token

    def get_request(self, url):
        oauth = self.get_client()
        uri, headers, body = oauth.sign("{}?limit=1000&key={}".format(url, self.Meta.client_key))
        return HTTPRequest(uri, headers=headers, body=body)

    @gen.coroutine
    def validate(self):
        if self.access_secret is None or self.access_token is None:
            return False, "missing token/secret"
        req = self.get_request('https://trello.com/1/members/me')
        try:
            client = AsyncHTTPClient()
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
            req = self.get_request("https://trello.com/1/members/me")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('fullName', 'Trello Account')
        except Exception:
            return "Trello Account"


class TrelloTokenAuth(Account):
    class Meta:
        identifier = "token"
        name = "Token Authentication"
        description = "Authentication via a manually-generated and supplied authentication token retrieved from Trello"

    token = TextField(name="Authentication Token", description="Auth token retrieved from Trello")
    token_link = LinkField(name="Token Page", default="https://trello.com/1/authorize?key={}&name=Vizydrop"
                                                      "&response_type=token".format(TrelloOAuth.Meta.client_key),
                           description="Navigate here to retrieve your access token:")

    def get_request(self, url):
        return HTTPRequest("{}?limit=1000&key={}&token={}".format(url, TrelloOAuth.Meta.client_key, self.token))

    @gen.coroutine
    def validate(self):
        if self.token is None:
            return False, "missing token"
        req = self.get_request('https://trello.com/1/members/me')
        try:
            client = AsyncHTTPClient()
            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except Exception as e:
            return False, e

    @gen.coroutine
    def get_friendly_name(self):
        try:
            client = AsyncHTTPClient()
            req = self.get_request("https://trello.com/1/members/me")
            resp = yield client.fetch(req)
            resp_data = json.loads(resp.body.decode('utf-8'))
            return resp_data.get('fullName', 'Trello Account')
        except Exception:
            return "Trello Account"
