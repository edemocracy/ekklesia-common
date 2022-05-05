# -*- coding: utf-8 -*-

import os
from datetime import datetime
from typing import Union

import case_conversion
from jinja2 import PackageLoader, PrefixLoader, Undefined
from jinja2.filters import pass_context
from markupsafe import Markup
import pypugjs.utils
import pypugjs.ext.jinja
from werkzeug.datastructures import ImmutableDict

from ekklesia_common import md


class JinjaAutoescapeCompiler(pypugjs.ext.jinja.Compiler):
    def visitCode(self, code):
        if code.buffer:
            val = code.val.lstrip()
            val = self.var_processor(val)
            self.buf.append(
                "%s%s%s" % (self.variable_start_string, val, self.variable_end_string)
            )
        else:
            self.buf.append("{%% %s %%}" % code.val)

        if code.block:
            self.visit(code.block)
            if not code.buffer:
                codeTag = code.val.strip().split(" ", 1)[0]
                if codeTag in self.auto_close_code:
                    self.buf.append("{%% end%s %%}" % codeTag)


class PugExtensionForBabel(pypugjs.ext.jinja.PyPugJSExtension):
    def preprocess(self, source, name, filename=None):
        return pypugjs.utils.process(
            source, filename=name, compiler=JinjaAutoescapeCompiler, **self.options
        )


class PugExtension(pypugjs.ext.jinja.PyPugJSExtension):

    file_extensions = [".jade", ".pug"]

    def preprocess(self, source, name, filename=None):
        if not name or (name and not os.path.splitext(name)[1] in
                                     PugExtension.file_extensions):
            return source
        jinja_code = pypugjs.utils.process(
            source, filename=name, compiler=JinjaAutoescapeCompiler, **self.options
        )
        return jinja_code


def select_jinja_autoescape(filename):
    """Returns `True` if autoescaping should be active for the given
    template name.

    !taken from Flask.
    """
    if filename is None:
        return False
    return filename.endswith((".html", ".htm", ".xml", ".xhtml", ".jade", ".pug"))


def format_datetime(timestamp_or_dt: Union[float, datetime]) -> str:
    """Format a timestamp for display."""
    if isinstance(timestamp_or_dt, datetime):
        return timestamp_or_dt.strftime("%Y-%m-%d @ %H:%M")
    else:
        return datetime.utcfromtimestamp(timestamp_or_dt).strftime("%Y-%m-%d @ %H:%M")


@pass_context
def yesno(context, val):
    request = context.get("_request")
    _ = request.i18n.gettext

    if val:
        return _("Yes")
    else:
        return _("No")


@pass_context
def enum_value(context, instance):
    request = context.get("_request")
    _ = request.i18n.gettext
    enum_name = case_conversion.snakecase(instance.__class__.__name__)

    if instance:
        return _(enum_name + "_" + case_conversion.snakecase(instance.value))
    else:
        return instance


def markdown(text):
    return Markup(md.convert(text))


def make_template_loader(app_config, package_name):
    loader_mapping = {
        p: PackageLoader(f"{package_name}.concepts.{p}") for p in app_config.concepts
    }
    template_loader = PrefixLoader(loader_mapping)
    return template_loader


def make_jinja_env(jinja_environment_class, jinja_options, app):
    def make_babel_filter(func_name):
        def babel_filter_wrapper(context, value):
            request = context.get("_request")
            func = getattr(request.i18n, func_name)
            return func(value)

        f = pass_context(babel_filter_wrapper)
        f.__name__ = func_name
        return f

    babel_filter_names = (
        ("datetimeformat", "format_datetime"),
        ("dateformat", "format_date"),
        ("numberformat", "format_number"),
        ("dateformat", "format_date"),
        ("timeformat", "format_time"),
        ("timedeltaformat", "format_timedelta"),
        ("decimalformat", "format_decimal"),
        ("currencyformat", "format_currency"),
        ("percentformat", "format_percent"),
        ("scientificformat", "format_scientific"),
    )
    babel_filters = {
        name: make_babel_filter(func_name) for name, func_name in babel_filter_names
    }

    default_jinja_options = ImmutableDict(
        extensions=[PugExtension, "jinja2.ext.autoescape", "jinja2.ext.i18n"],
        autoescape=select_jinja_autoescape,
    )

    jinja_env = jinja_environment_class(**default_jinja_options, **jinja_options)
    jinja_env.filters.update(babel_filters)
    jinja_env.filters["markdown"] = markdown
    jinja_env.filters["yesno"] = yesno
    jinja_env.filters["enum_value"] = enum_value

    def jinja_ngettext(s, p, n):
        # using the translation for zero is better than throwing an exception when
        # the number is undefined, I think
        if isinstance(n, Undefined):
            n = 0
        return app.babel.domain.get_translations().ungettext(s, p, n)

    def jinja_gettext(x):
        return app.babel.domain.get_translations().ugettext(x)

    jinja_env.install_gettext_callables(jinja_gettext, jinja_ngettext, newstyle=True)
    return jinja_env
