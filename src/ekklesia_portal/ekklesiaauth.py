from morepath import redirect, App, reify, Request
from requests_oauthlib import OAuth2Session
from urllib.parse import urljoin


class EkklesiaNotAuthorized(Exception):
    pass


class EkklesiaAuthRequest(Request):

    def __init__(self, environ, app, **kw):
        Request.__init__(self, environ, app, **kw)
        self.ekklesia_auth = EkklesiaAuth(self.app.settings.ekklesiaauth, self.browser_session)


class EkklesiaAuth:

    def __init__(self, settings, browser_session):
        self.browser_session = browser_session
        self.settings = settings

    @reify
    def session(self):
        if not self.authorized:
            raise EkklesiaNotAuthorized()

        extra = {'client_secret': self.settings.client_secret}
        return OAuth2Session(token=self._get_token(),
                             client_id=self.settings.client_id,
                             auto_refresh_url=self.settings.token_url,
                             auto_refresh_kwargs=extra,
                             token_updater=self._update_token)

    @property
    def authorized(self):
        return 'oauth_token' in self.browser_session

    def api_request(self, method, path, **kwargs):
        url = urljoin(self.settings.api_base_url, path)
        res = self.session.request(method, url, **kwargs)
        return res.json()

    @reify
    def profile(self):
        return self.api_request('GET', 'profile')

    @reify
    def auid(self):
        return self.api_request('GET', 'auid')

    @reify
    def membership(self):
        return self.api_request('GET', 'membership')

    def _update_token(self, token):
        self.browser_session['oauth_token'] = token

    def _get_token(self):
        return self.browser_session.get('oauth_token')


class EkklesiaAuthApp(App):
    pass


@EkklesiaAuthApp.setting_section(section='ekklesiaauth')
def ekklesia_auth_setting_section():
    return {
        'client_id': 'ekklesia_portal',
        'client_secret': "ekklesia_portal_secret",
        'api_base_url': "https://identity-server.invalid/api/v1/",
        'authorization_url': "https://identity-server.invalid/oauth2/authorize/",
        'token_url': "https://identity-server.invalid/oauth2/token/"
    }


class OAuthLogin:
    def __init__(self, settings, session):
        self.settings = settings
        self.session = session
        self.oauth = OAuth2Session(client_id=settings.client_id)

    def get_authorization_url(self):
        authorization_url, state = self.oauth.authorization_url(self.settings.authorization_url)
        self.session["oauth_state"] = state
        return authorization_url


@EkklesiaAuthApp.path(model=OAuthLogin, path="/login")
def oauth_login(request):
    return OAuthLogin(request.app.settings.ekklesiaauth, request.browser_session)


@EkklesiaAuthApp.view(model=OAuthLogin)
def get_oauth_login(self, _):
    """redirect to login URL on ekklesia ID server"""
    return redirect(self.get_authorization_url())


class OAuthCallback:
    def __init__(self, settings, session, base_callback_url, called_url):
        self.settings = settings
        self.called_url = called_url
        self.session = session
        self.oauth = OAuth2Session(client_id=settings.client_id, redirect_uri=base_callback_url, state=session.get('oauth_state'))

    @property
    def redirect_after_success_url(self):
        return "/"

    def set_token(self, token):
        self.session['oauth_token'] = token

    def fetch_token(self):
        token = self.oauth.fetch_token(token_url=self.settings.token_url,
                                       authorization_response=self.called_url,
                                       client_secret=self.settings.client_secret)

        self.set_token(token)


@EkklesiaAuthApp.path(model=OAuthCallback, path="/callback")
def oauth_callback(request):
    return OAuthCallback(request.app.settings.ekklesiaauth,
                         request.browser_session,
                         request.class_link(OAuthCallback),
                         request.url)


@EkklesiaAuthApp.view(model=OAuthCallback)
def get_oauth_callback(self, _):
    self.fetch_token()
    return redirect(self.redirect_after_success_url)


class OAuthInfo:
    def __init__(self, ekklesia_auth):
        self.ekklesia_auth = ekklesia_auth


@EkklesiaAuthApp.path(model=OAuthInfo, path="/info")
def oauth_info(request):
    return OAuthInfo(request.ekklesia_auth)


@EkklesiaAuthApp.json(model=OAuthInfo)
def oauth_info_json(self, _):
    return {
        'membership': self.ekklesia_auth.membership,
        'profile': self.ekklesia_auth.profile,
        'auid': self.ekklesia_auth.auid,
    }
