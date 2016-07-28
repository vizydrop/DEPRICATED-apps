from urllib import parse
from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPError
from tornado import gen

from vizydrop.sdk.account import Account, AppHTTPBasicAuthAccount
from vizydrop import fields

import json


class TargetprocessBasicAuth(AppHTTPBasicAuthAccount):
    class Meta:
        identifier = 'basic'
        name = "HTTP-Basic Authentication"
        description = "Basic HTTP authentication for access to Targetprocess"

    tp_url = fields.URLField(name="TP Path", description="Path to your Targetprocess instance", optional=False)

    def get_request(self, url, headers=None, **kwargs):
        if not headers:
            headers = {}
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return HTTPRequest(url, headers=headers, **kwargs)

    @property
    def tp_host(self):
        parsed = parse.urlparse(self.tp_url)
        return parsed.hostname or self.tp_url

    @gen.coroutine
    def validate(self):
        if not self.tp_url:
            raise ValueError("required field tp_url missing")
        try:
            client = AsyncHTTPClient()

            uri = "{}/api/v1/Authentication".format(self.tp_url)
            req = self.get_request(uri)

            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except HTTPError as e:
            return False, e.response

    @gen.coroutine
    def get_friendly_name(self):
        if not self.tp_url:
            raise ValueError("required field tp_url missing")
        try:
            client = AsyncHTTPClient()
            uri = "{}/api/v1/Users?where=Login eq '{}'&take=[FirstName,LastName]".format(self.tp_url, self.username)
            req = self.get_request(uri)
            resp = yield client.fetch(req)
            data = json.loads(resp.body.decode('utf-8'))
            user_fullname = ' '.join([data['Value'][0]['FirstName'], data['Value'][0]['LastName']])
            return "{} ({})".format(user_fullname, self.tp_host)
        except:
            return "{} @ {}".format(self.username, self.tp_host)


class TargetproessTokenAuth(Account):
    class Meta:
        identifier = 'token'
        name = "API Token Authentication"
        description = "Token authentication for access to Targetprocess"

    tp_url = fields.URLField(name="TP Path", description="Path to your Targetprocess instance", optional=False)
    token_link = fields.LinkField(name="More details", default="http://dev.targetprocess.com/rest/authentication#token",
                                  description="To get your API token, navigate to [your tp instance]/api/v1/authentication")
    token = fields.TextField(name="API Token", description="API Token from Targetprocess", optional=False)

    def get_request(self, url, headers=None, **kwargs):
        url = ('&' if '?' in url else '?').join([url, 'token={}'.format(self.token)])
        if not headers:
            headers = {}
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return HTTPRequest(url, headers=headers, **kwargs)

    @property
    def tp_host(self):
        parsed = parse.urlparse(self.tp_url)
        return parsed.hostname or self.tp_url

    @gen.coroutine
    def validate(self):
        if not self.tp_url:
            raise ValueError("required field tp_url missing")
        try:
            client = AsyncHTTPClient()

            uri = "{}/api/v1/Authentication".format(self.tp_url)
            req = self.get_request(uri)

            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except HTTPError as e:
            return False, e.response

    @gen.coroutine
    def get_friendly_name(self):
        if not self.tp_url:
            raise ValueError("required field tp_url missing")
        try:
            client = AsyncHTTPClient()

            uri = "{}/api/v1/Context?format=json".format(self.tp_url)
            req = self.get_request(uri)

            resp = yield client.fetch(req)
            data = json.loads(resp.body.decode('utf-8'))
            user_fullname = ' '.join([data['LoggedUser']['FirstName'], data['LoggedUser']['LastName']])
            return "{} ({})".format(user_fullname, self.tp_host)
        except:
            return "{} (API Token)".format(self.tp_host)
