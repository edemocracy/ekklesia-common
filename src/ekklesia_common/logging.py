from io import StringIO
import logging
import os
import sys
import inspect
import traceback

import eliot
from eliot.json import EliotJSONEncoder
from eliot.stdlib import EliotHandler

from ekklesia_common.app import UnhandledRequestException

class EkklesiaLogEncoder(EliotJSONEncoder):

    def default(self, obj):

        try:
            return EliotJSONEncoder.default(self, obj)
        except TypeError:
            return repr(obj)

if os.environ.get("BETTER_EXCEPTIONS"):
    import better_exceptions.formatter
    import better_exceptions.color
    formatter = better_exceptions.formatter.ExceptionFormatter(
        colored=better_exceptions.color.SUPPORTS_COLOR,
        theme=better_exceptions.formatter.THEME,
        max_length=better_exceptions.formatter.MAX_LENGTH,
        pipe_char=better_exceptions.formatter.PIPE_CHAR,
        cap_char=better_exceptions.formatter.CAP_CHAR)

    def _format_traceback(tb) -> str:
        return "".join(formatter.format_traceback(tb))
else:

    def _format_traceback(tb) -> str:
        sio = StringIO()

        traceback.print_tb(tb, None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]

        return s


# Idea taken from: https://github.com/itamarst/eliot/issues/394
EXCLUDED_EXCEPTION_MEMBERS = set(dir(Exception())) | {"__weakref__", "__module__"}

def _get_exception_data(exc: BaseException):
    # Exclude the attributes that appear on a regular exception,
    # aside from a few interesting ones.
    if hasattr(exc, "__structlog__"):
        return exc.__structlog__()
    else:
        return {k: v for k, v in inspect.getmembers(exc) if k not in EXCLUDED_EXCEPTION_MEMBERS}


def _exception_data_and_traceback(exc: Exception) -> dict[str, str]:
    exception_class = type(exc)
    data = {
        "exception": exception_class.__module__ + "." + exception_class.__name__
    }

    if isinstance(exc, UnhandledRequestException):
        data["xid"] = exc.xid
    else:
        data["traceback"] = 'Traceback (most recent call last):\n' + _format_traceback(exc.__traceback__)
        exception_data = _get_exception_data(exc)
        if exception_data:
            data["data"] = exception_data
        data["reason"] = str(exc)

    return data

def _add_exception_data_and_traceback(exc: Exception):
    try:
        event_dict = _exception_data_and_traceback(exc)
        if exc.__cause__:
            event_dict["cause"] = _exception_data_and_traceback(exc.__cause__)

        if exc.__context__ is not None and not exc.__suppress_context__:
            event_dict["context"] = _exception_data_and_traceback(exc.__context__)

        return event_dict

    except Exception as e:
        return {
            "log_error": "While trying to extract and format exception metadata, another exception occurred",
            "log_error_msg": f"{type(e).__name__}: {e}",
            "log_error_traceback": _format_traceback(e.__traceback__)
        }

def init_logging():
    eliot.register_exception_extractor(Exception, _add_exception_data_and_traceback)

    root_logger = logging.getLogger()
    root_logger.addHandler(EliotHandler())
    root_logger.setLevel(logging.DEBUG)
    logging.getLogger("morepath.directive").setLevel(logging.INFO)
    logging.getLogger("passlib.registry").setLevel(logging.INFO)
    logging.getLogger("passlib.utils.compat").setLevel(logging.INFO)
    logging.getLogger("parso").setLevel(logging.WARN)

    eliot.to_file(sys.stderr, encoder=EkklesiaLogEncoder)

    logging.captureWarnings(True)

