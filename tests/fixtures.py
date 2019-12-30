import logging
import os.path
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
