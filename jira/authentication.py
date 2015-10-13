from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPError
from tornado import gen

from vizydrop.fields import URLField
from vizydrop.sdk.account import AppHTTPBasicAuthAccount


class JIRABasicAuth(AppHTTPBasicAuthAccount):
    class Meta:
        identifier = 'basic'
        name = "HTTP-Basic Authentication"
        description = "Basic HTTP authentication for access to JIRA"

    jira_url = URLField(name='URL', optional=False, description='URL path to your JIRA server/instance')

    def get_request(self, url, headers=None, **kwargs):
        if not headers:
            headers = {}
        headers['Authorization'] = "Basic {}".format(self._get_basic_auth())
        return HTTPRequest(url, headers=headers, **kwargs)

    @gen.coroutine
    def validate(self):
        if self.jira_url is None:
            return False, 'missing JIRA url'
        try:
            client = AsyncHTTPClient()
            jira_url = self.jira_url
            req = self.get_request("{}/rest/api/2/myself".format(jira_url.rstrip('/')))
            resp = yield client.fetch(req)
            if 200 <= resp.code < 300:
                return True, None
            else:
                return False, resp.body.decode('utf-8')
        except HTTPError as e:
            return False, e.response.reason

    def get_friendly_name(self):
        return "{} @ {}".format(self.username, self.jira_url)
