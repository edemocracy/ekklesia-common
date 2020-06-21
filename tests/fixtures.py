import logging
from unittest.mock import Mock
import os.path
from munch import Munch
from pytest import fixture
from morepath.request import BaseRequest
import morepath
from ekklesia_common.app import EkklesiaApp
from ekklesia_common.request import EkklesiaRequest
from types import SimpleNamespace as N


BASEDIR = os.path.dirname(__file__)
logg = logging.getLogger(__name__)


@fixture(scope="session")
def app():
    morepath.autoscan()
    EkklesiaApp.commit()
    app = EkklesiaApp()
    app.babel_init()
    return app


@fixture
def req(app):
    environ = BaseRequest.blank('test').environ
    return EkklesiaRequest(environ, app)


@fixture
def request_for_cell(app):
    return N(
        app=N(settings=N(), get_cell_class=None),
        current_user=N(),
        i18n=N(gettext=None),
        render_template=None)


@fixture
def model():
    class TestModel(Munch):
        pass

    return TestModel(id=5, title="test", private="secret")

