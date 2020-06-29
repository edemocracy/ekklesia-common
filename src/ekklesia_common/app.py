import logging
import os

import morepath
from more.babel_i18n import BabelApp
from more.browser_session import BrowserSessionApp
import yaml

from ekklesia_common import database
from ekklesia_common.cell import JinjaCellEnvironment
from ekklesia_common.cell_app import CellApp
from ekklesia_common.concept import ConceptApp
from ekklesia_common.contract import FormApp
from ekklesia_common.templating import make_jinja_env, make_template_loader
from ekklesia_common.request import EkklesiaRequest


logg = logging.getLogger(__name__)


class EkklesiaApp(ConceptApp, BabelApp, BrowserSessionApp, FormApp, CellApp):
    request_class = EkklesiaRequest


def get_locale(request):
    locale = request.browser_session.get('lang')
    if locale:
        logg.debug('locale from session: %s', locale)
    else:
        locale = request.accept_language.best_match(['de', 'en', 'fr'])
        logg.debug('locale from request: %s', locale)

    return locale

