import datetime
import logging
from ekklesia_common.app import App
from ..cell.page_test import PageTestCell


logg = logging.getLogger(__name__)


class PageTest:
    pass


@App.path(model=PageTest, path="page_test")
def page_test():
    return PageTest()


@App.html(model=PageTest)
def show(self, request):
    request.browser_session['old'] = request.browser_session.get('test')
    request.browser_session['test'] = datetime.datetime.now().isoformat()
    return PageTestCell(self, request).show()
