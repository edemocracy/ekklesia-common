import logging
import os

import morepath
from more.babel_i18n import BabelApp
from more.browser_session import BrowserSessionApp
from more.forwarded import ForwardedApp
from more.transaction import TransactionApp
import yaml

from ekklesia_common import database
from ekklesia_common.cell import JinjaCellEnvironment
from ekklesia_common.concept import ConceptApp
from ekklesia_common.contract import FormApp
from ekklesia_common.templating import make_jinja_env, make_template_loader
from ekklesia_common.identity_policy import EkklesiaIdentityPolicy
from ekklesia_common.request import EkklesiaRequest


logg = logging.getLogger(__name__)


class App(ConceptApp, ForwardedApp, TransactionApp, BabelApp, BrowserSessionApp, FormApp):
    request_class = EkklesiaRequest

    def __init__(self):
        super().__init__()
        self.jinja_env = make_jinja_env(jinja_environment_class=JinjaCellEnvironment,
                                        jinja_options=dict(loader=make_template_loader(App.config, 'ekklesia_common')),
                                        app=self)

@App.identity_policy()
def get_identity_policy():
    return EkklesiaIdentityPolicy()


@App.verify_identity()
def verify_identity(identity):
    return True


def get_app_settings(settings_filepath):
    from ekklesia_common.default_settings import settings

    if settings_filepath is None:
        logg.info("no config file given")
    elif os.path.isfile(settings_filepath):
        with open(settings_filepath) as config:
            settings_from_file = yaml.safe_load(config)
        logg.info("loaded config from %s", settings_filepath)

        for section_name, section in settings_from_file.items():
            if section_name in settings:
                settings[section_name].update(section)
            else:
                settings[section_name] = section
    else:
        logg.warn("config file path %s doesn't exist!", settings_filepath)

    return settings


def get_locale(request):
    locale = request.browser_session.get('lang')
    if locale:
        logg.debug('locale from session: %s', locale)
    else:
        locale = request.accept_language.best_match(['de', 'en', 'fr'])
        logg.debug('locale from request: %s', locale)

    return locale


def make_wsgi_app(settings_filepath=None, testing=False):
    morepath.autoscan()
    settings = get_app_settings(settings_filepath)
    App.init_settings(settings)
    App.commit()

    app = App()
    database.configure_sqlalchemy(app.settings.database, testing)
    app.babel_init()
    app.babel.localeselector(get_locale)
    return app
