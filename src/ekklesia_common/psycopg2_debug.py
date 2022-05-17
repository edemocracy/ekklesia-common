"""
Some debugging extensions for Psycopg2.
"""
import time
from dataclasses import dataclass

from decorator import contextmanager
from eliot import log_message
from psycopg2.extensions import connection as _connection
from psycopg2.extensions import cursor as _cursor

# used for SQL formatting, if present
try:
    import pygments
except ImportError:
    pygments = None

DEFAULT_PYGMENTS_STYLE = "native"


def _make_statement_formatter(
    show_time, highlight, pygments_style, prefix=None, formatter_cls=None
):
    def format_stmt(sql, timestamp=0, duration=0.0):
        if show_time:
            msg = "{:.2f} ({:.2f}ms): {}".format(
                timestamp, duration * 1000, sql.strip()
            )
            if prefix:
                return prefix + msg
            else:
                return msg
        else:
            if prefix:
                return prefix + sql
            else:
                return sql

    if highlight and pygments:
        from pygments.lexers import PostgresLexer

        lexer = PostgresLexer()

        if formatter_cls is None:
            from pygments.formatters import Terminal256Formatter

            formatter_cls = Terminal256Formatter

        formatter = formatter_cls(style=pygments_style)

        def highlight_format_stmt(sql, timestamp=0, duration=0):
            return pygments.highlight(
                format_stmt(sql, timestamp, duration), lexer, formatter
            )

        return highlight_format_stmt
    else:
        return format_stmt


@dataclass
class StatementEntry:
    sql: str
    duration: float
    timestamp: int
    notices: list[str]


class StatementHistory(object):
    """
    Keeps a history of SQL statements with execution time and offers some pretty
    printing options.
    """

    entries: list[StatementEntry]

    def __init__(self):
        self.entries = []

    def append(self, sql, timestamp, duration, notices):
        entry = StatementEntry(sql, duration, timestamp, notices)
        self.entries.append(entry)

    def overall_duration_ms(self):
        return sum(e.duration for e in self.entries) * 1000

    def __len__(self):
        return len(self.entries)

    def clear(self):
        self.entries.clear()

    @property
    def last_statement(self):
        if self.entries:
            return self.entries[-1]

    @property
    def sql_statements(self):
        return [e.sql for e in self.entries]

    def format_statement(
        self,
        stmt,
        highlight=True,
        time=0,
        duration=0.0,
        pygments_style=DEFAULT_PYGMENTS_STYLE,
        prefix=None,
        formatter_cls=None,
    ):
        show_time = time and duration
        highlight_format_stmt = _make_statement_formatter(
            show_time, highlight, pygments_style, prefix, formatter_cls
        )
        return highlight_format_stmt(stmt, time, duration)

    def print_last_statement(
        self, show_time=True, highlight=True, pygments_style=DEFAULT_PYGMENTS_STYLE
    ):

        entry = self.last_statement
        if entry is None:
            print("history is empty")
            return

        highlight_format_stmt = _make_statement_formatter(
            show_time, highlight, pygments_style
        )
        print(highlight_format_stmt(entry.sql, entry.timestamp, entry.duration))

    def print_statements(
        self,
        show_time=True,
        highlight=True,
        pygments_style=DEFAULT_PYGMENTS_STYLE,
        prefix=None,
    ):
        if not self.entries:
            print("history is empty")
            return

        highlight_format_stmt = _make_statement_formatter(
            show_time, highlight, pygments_style, prefix
        )

        for entry in self.entries:
            print(highlight_format_stmt(entry.sql, entry.timestamp, entry.duration))


class DebugCursor(_cursor):
    """A cursor that logs queries with execution timestamp and duration,
    using its connection logging facilities.
    """

    @contextmanager
    def _logging(self):
        start_ts = time.time()
        yield
        end_ts = time.time()
        duration = end_ts - start_ts
        self.connection.log(self.query.decode("utf8"), end_ts, duration, self)

    def execute(self, query, vars=None):
        with self._logging():
            return super(DebugCursor, self).execute(query, vars)

    def callproc(self, procname, vars=None):
        with self._logging():
            return super(DebugCursor, self).callproc(procname, vars)


def make_debug_connection_factory():
    """Creates a DebugConnection which can be used as connection_factory for
    Psycopg2.connect()
    """

    class DebugConnection(_connection):
        """Psycopg2 connection which keeps a history of SQL statements and logs them.
        Inspired by psycopg2.extras.LoggingConnection
        """

        def log(self, sql, timestamp, duration, curs):
            notices = [notice.strip() for notice in self.notices]
            duration_ms = duration * 1000
            duration_formatted = f"{duration_ms:.2f}ms"
            log_entry = dict(duration=duration_formatted, duration_ms=duration, sql=sql)
            if notices:
                log_entry["notices"] = notices
            log_message("sql-statement", **log_entry)
            self._history.append(sql, timestamp, duration, notices)

        def _create_missing_history(self):
            if not hasattr(self, "_history"):
                self._history = StatementHistory()

        @property
        def history(self):
            self._create_missing_history()
            return self._history

        def cursor(self, *args, **kwargs):
            self._create_missing_history()
            kwargs.setdefault("cursor_factory", DebugCursor)
            return super(DebugConnection, self).cursor(*args, **kwargs)

    return DebugConnection
