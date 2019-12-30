from ekklesia_common.cell import Cell


class LayoutCell(Cell):

    def language(self):
        return self._request.i18n.get_locale().language

    def brand_title(self):
        return self._s.app.title

    def profile_url(self):
        return self.link(self.current_user)

    def custom_footer_url(self):
        return self._s.app.custom_footer_url

    def tos_url(self):
        return self._s.app.tos_url

    def faq_url(self):
        return self._s.app.faq_url

    def imprint_url(self):
        return self._s.app.imprint_url

    def source_code_url(self):
        return 'https://github.com/dpausp/ekklesia-common'
