import logging
import os.path
from types import SimpleNamespace as N

import morepath
from morepath.request import BaseRequest
from munch import Munch
from pytest import fixture

from ekklesia_common.app import EkklesiaBrowserApp
from ekklesia_common.request import EkklesiaRequest


import more.babel_i18n
import more.browser_session

BASEDIR = os.path.dirname(__file__)
logg = logging.getLogger(__name__)


@fixture(scope="session")
def app():
    morepath.scan(more.babel_i18n)
    morepath.scan(more.browser_session)
    #morepath.autoscan(ignore=["more-babel-i18n", "more-browser-session", "more_babel_i18n", "more_browser_session"])
    EkklesiaBrowserApp.commit()
    app = EkklesiaBrowserApp()
    app.babel_init()
    return app


@fixture
def req(app):
    environ = BaseRequest.blank("test").environ
    return EkklesiaRequest(environ, app)


@fixture
def request_for_cell(app):
    return N(
        app=N(settings=N(), get_cell_class=None),
        current_user=N(),
        i18n=N(gettext=None),
        render_template=None,
    )

from munch import Munch

class ATestModel(Munch):
    pass

@fixture
def model():
    return ATestModel(id=5, title="test", private="secret")
