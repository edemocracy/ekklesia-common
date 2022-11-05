import sys
import morepath
import more.babel_i18n
import more.browser_session
import more.forwarded


def morepath_scan_deps():
    morepath.scan(morepath)
    morepath.scan(more.babel_i18n)
    morepath.scan(more.browser_session)
    morepath.scan(more.forwarded)
    morepath.scan(sys.modules[__name__])
