import json
import logging
import re
import webbrowser
import wsgiref.simple_server
import wsgiref.util

import requests_oauthlib

from gears_testing.api.strava.utils import _request

_LOGGER = logging.getLogger(__name__)


"""
Code inspired by Google's OAuth 2.0 Authorization Flow codebase
"""


class Flow(object):

    def __init__(
        self,
        oauth2session,
        config,
        redirect_uri=None
    ):

        self.config = config
        """Mapping[str, Any]: The OAuth 2.0 client configuration."""
        self.oauth2session = oauth2session
        """requests_oauthlib.OAuth2Session: The OAuth 2.0 session."""
        self.redirect_uri = redirect_uri

    @classmethod
    def from_client_config(cls, config, scopes, **kwargs):
        session = requests_oauthlib.OAuth2Session(client_id=config["client_id"], scope=scopes, **kwargs)
        return cls(session, config)

    @classmethod
    def from_client_secrets_file(cls, client_secrets_file, scopes, **kwargs):
        with open(client_secrets_file, "r") as json_file:
            client_config = json.load(json_file)
        return cls.from_client_config(client_config, scopes=scopes, **kwargs)

    @property
    def redirect_uri(self):
        return self.oauth2session.redirect_uri

    @redirect_uri.setter
    def redirect_uri(self, value):
        self.oauth2session.redirect_uri = value

    def authorization_url(self, **kwargs):
        kwargs.setdefault("access_type", "offline")
        url, state = self.oauth2session.authorization_url(self.config["auth_uri"], **kwargs)
        return url, state

    def fetch_token(self, **kwargs):
        res = kwargs.get('authorization_response', '')
        pattern = r"(?<=code=)\w+(?=&scope)"
        code = re.search(pattern, res).group() or ''
        return self.exchange_token(
            client_id=self.config.get('client_id'),
            client_secret=self.config.get('client_secret'),
            grant_type="authorization_code",
            code=code
        )

    def exchange_token(self, **kwargs):
        res = _request(self.oauth2session,
                       "POST",
                       "https://www.strava.com/oauth/token",
                       params=kwargs)
        self.config['access_token'] = res.get('access_token')
        self.config['refresh_token'] = res.get('refresh_token')
        self.config['expires_at'] = res.get('expires_at')

    @property
    def credentials(self):
        return self.config


class InstalledAppFlow(Flow):
    _DEFAULT_AUTH_PROMPT_MESSAGE = (
        "Please visit this URL to authorize this application: {url}"
    )
    """str: The message to display when prompting the user for
    authorization."""
    _DEFAULT_AUTH_CODE_MESSAGE = "Enter the authorization code: "
    """str: The message to display when prompting the user for the
    authorization code. Used only by the console strategy."""

    _DEFAULT_WEB_SUCCESS_MESSAGE = (
        "The authentication flow has completed. You may close this window."
    )

    def run_local_server(
        self,
        host="localhost",
        bind_addr=None,
        port=8080,
        authorization_prompt_message=_DEFAULT_AUTH_PROMPT_MESSAGE,
        success_message=_DEFAULT_WEB_SUCCESS_MESSAGE,
        open_browser=True,
        redirect_uri_trailing_slash=True,
        timeout_seconds=None,
        **kwargs
    ):
        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            bind_addr or host, port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        redirect_uri_format = (
            "http://{}:{}/" if redirect_uri_trailing_slash else "http://{}:{}"
        )
        self.redirect_uri = redirect_uri_format.format(host, local_server.server_port)
        auth_url, _ = self.authorization_url(**kwargs)

        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)

        if authorization_prompt_message:
            print(authorization_prompt_message.format(url=auth_url))

        local_server.timeout = timeout_seconds
        local_server.handle_request()

        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        self.fetch_token(authorization_response=authorization_response)

        local_server.server_close()

        return self.credentials


class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        _LOGGER.info(format, *args)


class _RedirectWSGIApp(object):

    def __init__(self, success_message):
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(self, environ, start_response):
        start_response("200 OK", [("Content-type", "text/plain; charset=utf-8")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]
