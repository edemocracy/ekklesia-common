import logging
from unittest.mock import Mock
import os.path
from munch import Munch
from pytest import fixture
from morepath.request import BaseRequest
import morepath
from ekklesia_common.app import make_wsgi_app
from ekklesia_common.request import EkklesiaRequest


BASEDIR = os.path.dirname(__file__)
logg = logging.getLogger(__name__)


@fixture(scope="session")
def app():
    app = make_wsgi_app(testing=True)
    return app


@fixture
def req(app):
    environ = BaseRequest.blank('test').environ
    return EkklesiaRequest(environ, app)


@fixture
def request_for_cell(app):
    environ = BaseRequest.blank('test').environ
    m = Mock(spec=EkklesiaRequest(environ, app))
    m.app = app
    m.i18n = Mock()
    return m


@fixture
def model():
    class TestModel(Munch):
        pass

    return TestModel(id=5, title="test", private="secret")

