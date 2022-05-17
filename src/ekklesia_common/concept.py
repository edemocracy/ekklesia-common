import sys
from functools import wraps
from typing import get_type_hints

import dectate
import morepath
from dectate import directive
from dectate.config import create_code_info
from eliot import start_action


class ConceptAction(dectate.Action):
    config = {"concepts": dict}

    def __init__(self, name):
        super().__init__()
        self.name = name

    def identifier(self, **_kw):
        return self.name

    def perform(self, obj, concepts):
        concepts[self.name] = obj


class ConceptApp(morepath.App):

    concept = directive(ConceptAction)

    @classmethod
    def html(
        cls,
        model=None,
        render=None,
        template=None,
        load=None,
        permission=None,
        internal=False,
        **predicates
    ):

        sup_html = super().html
        model_outer = model

        def decorator(fn):

            if model_outer:
                model = model_outer
            else:
                model = get_type_hints(fn)["self"]

            sup_decorator = sup_html(
                model, render, template, load, permission, internal, **predicates
            )

            frame = sys._getframe(1)
            code_info = create_code_info(frame)
            sup_decorator.code_info = code_info

            fn_path = fn.__module__.split(".")

            if fn_path[1] == "concepts":
                ctx = {
                    "app": fn_path[0],
                    "concept": fn_path[2].capitalize(),
                    "view": fn.__qualname__,
                }
            else:
                ctx = {"module": fn.__module__, "view": fn.__qualname__}

            @wraps(fn)
            def log_wrapper(*args, **kwargs):

                model = args[0]
                model_data = model.to_dict() if hasattr(model, "to_dict") else model

                ctx["model"] = model_data

                with start_action(action_type="html_view", **ctx):
                    return fn(*args, **kwargs)

            return sup_decorator(log_wrapper)

        return decorator
