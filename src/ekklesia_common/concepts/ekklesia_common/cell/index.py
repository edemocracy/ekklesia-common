from ekklesia_common.concepts.ekklesia_common.cell.layout import LayoutCell
from ekklesia_common.concepts.ekklesia_common.view.page_test import PageTest


class IndexCell(LayoutCell):

    def page_test_url(self):
        return self.class_link(PageTest, {})