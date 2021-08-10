from datetime import datetime
import secrets
from functools import cached_property
from pkg_resources import resource_filename

from eliot import start_task, log_message
import morepath
from webob.exc import HTTPError
from more.babel_i18n import BabelApp
from more.browser_session import BrowserSessionApp
from more.forwarded import ForwardedApp
from more.transaction import TransactionApp

from ekklesia_common.errors import exception_uid
from ekklesia_common.cell import JinjaCellEnvironment
from ekklesia_common.cell_app import CellApp
from ekklesia_common.concept import ConceptApp
from ekklesia_common.contract import FormApp
from ekklesia_common.ekklesia_auth import EkklesiaAuthApp
from ekklesia_common.identity_policy import NoIdentity
from ekklesia_common.lid import LID
from ekklesia_common.permission import WritePermission
from ekklesia_common.templating import make_jinja_env, make_template_loader
from ekklesia_common.request import EkklesiaRequest


class EkklesiaBrowserApp(BabelApp, BrowserSessionApp, CellApp, ConceptApp, EkklesiaAuthApp, FormApp, ForwardedApp,
                         TransactionApp):

    request_class = EkklesiaRequest
    package_name = 'ekklesia_common'

    @cached_property
    def translation_dir(self):
        return resource_filename(self.package_name, 'translations/')

    def __init__(self):
        super().__init__()
        template_loader = make_template_loader(self.__class__.config, self.__class__.package_name)
        self.jinja_env = make_jinja_env(
            jinja_environment_class=JinjaCellEnvironment, jinja_options=dict(loader=template_loader), app=self)


@EkklesiaBrowserApp.permission_rule(model=object, permission=WritePermission, identity=NoIdentity)
def has_write_permission_not_logged_in(identity, model, permission):
    """Protects all views with write actions from users that aren't logged in."""
    return False


@EkklesiaBrowserApp.setting_section(section="browser_session")
def browser_session_setting_section():
    return {
        "secret_key": secrets.token_urlsafe(64),
        "cookie_secure": True,
    }


@EkklesiaBrowserApp.setting_section(section='common')
def common_setting_section():
    """Various settings that can be used by ekklesia-common code."""
    return {
        "fail_on_form_validation_error": False,
        "force_ssl": False,
        "instance_name": "ekklesia_app",
    }


@EkklesiaBrowserApp.setting_section(section='database')
def database_setting_section():
    """Database config for SQLAlchemy/psycopg2"""
    return {
        "enable_statement_history": False,
        "print_sql_statements": False,
    }


@EkklesiaBrowserApp.setting_section(section="static_files")
def static_files_setting_section():
    return {"base_url": "/static"}

class UnhandledRequestException(RuntimeError):

    def __init__(self, task_uuid, xid):
        self.task_uuid = task_uuid
        self.xid = xid
        super().__init__(f"XID {xid}")



@EkklesiaBrowserApp.tween_factory()
def make_ekklesia_log_tween(app: EkklesiaBrowserApp, handler):
    db_settings = app.settings.database

    print_sql_statements = db_settings.enable_statement_history and db_settings.print_sql_statements

    def ekklesia_log_tween(request):
        request_data = {'url': request.url, 'headers': dict(request.headers)}

        user = request.current_user

        if user is not None:
            request_data['user'] = user.id

        with start_task(action_type='request', request=request_data) as task:
            try:
                if print_sql_statements:
                    history = request.db_session.connection().connection.connection.history
                    history.clear()
                response = handler(request)

                if print_sql_statements:
                    print()
                    print(f"{SQL_PRINT_PREFIX}SQL statements for this request")
                    history.print_statements(prefix=SQL_PRINT_PREFIX)
                    print(
                        f"{SQL_PRINT_PREFIX}{len(history)} SQL statements, duration {history.overall_duration_ms():.2f}ms"
                    )
                    print()
                return response
            except HTTPError:
                # Let Morepath handle this (exception views).
                raise
            except Exception as e:
                # Something else failed, wrap the exception and add metadata for better error reporting.
                datetime_now = datetime.now()
                suffix = task.task_uuid[:7]
                xid = exception_uid(e, datetime_now, suffix)
                raise UnhandledRequestException(task.task_uuid, xid) from e

    return ekklesia_log_tween


@EkklesiaBrowserApp.tween_factory()
def make_ekklesia_customizations_tween(app, handler):
    def ekklesia_customizations_tween(request):
        if app.settings.common.force_ssl:
            request.scheme = 'https'

        return handler(request)

    return ekklesia_customizations_tween


@EkklesiaBrowserApp.converter(type=LID)
def convert_lid():
    return morepath.Converter(lambda s: LID.from_str(s), lambda l: str(l))


def get_locale(request):
    locale = request.browser_session.get('lang')
    if locale:
        logg.debug('locale from session: %s', locale)
    else:
        locale = request.accept_language.best_match(['de', 'en', 'fr'])
        logg.debug('locale from request: %s', locale)

    return locale
