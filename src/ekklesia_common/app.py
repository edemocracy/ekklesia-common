import logging
import os
from pkg_resources import resource_filename

import morepath
from more.babel_i18n import BabelApp
from more.browser_session import BrowserSessionApp
from more.forwarded import ForwardedApp
from more.transaction import TransactionApp
import yaml

from ekklesia_common import database
from ekklesia_common.cell import JinjaCellEnvironment
from ekklesia_common.cell_app import CellApp
from ekklesia_common.concept import ConceptApp
from ekklesia_common.contract import FormApp
from ekklesia_common.ekklesia_auth import EkklesiaAuthApp
from ekklesia_common.templating import make_jinja_env, make_template_loader
from ekklesia_common.request import EkklesiaRequest
from ekklesia_common.utils import cached_property

logg = logging.getLogger(__name__)


class EkklesiaBrowserApp(BabelApp, BrowserSessionApp, CellApp, ConceptApp, EkklesiaAuthApp, FormApp, ForwardedApp, TransactionApp):

    request_class = EkklesiaRequest
    package_name = 'ekklesia_common'

    @cached_property
    def translation_dir(self):
        return resource_filename(self.package_name, 'translations/')

    def __init__(self):
        super().__init__()
        template_loader = make_template_loader(self.__class__.config, self.__class__.package_name)
        self.jinja_env = make_jinja_env(jinja_environment_class=JinjaCellEnvironment,
                                        jinja_options=dict(loader=template_loader),
                                        app=self)


def get_locale(request):
    locale = request.browser_session.get('lang')
    if locale:
        logg.debug('locale from session: %s', locale)
    else:
        locale = request.accept_language.best_match(['de', 'en', 'fr'])
        logg.debug('locale from request: %s', locale)

    return locale
