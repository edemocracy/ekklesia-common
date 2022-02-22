from functools import cached_property
from typing import Any
import morepath
from eliot import start_action
from ekklesia_common import database
from ekklesia_common.permission import Permission
from jinja2 import Template
from sqlalchemy.orm import Session, Query

class RenderTemplateError(Exception):
    def __init__(self, template_name, cause) -> None:
        self.template_name = template_name
        cause_type = type(cause).__name__
        msg = f"Template {template_name} could not be rendered because of an exception: {cause_type}: {cause}"
        super().__init__(msg)

class EkklesiaRequest(morepath.Request):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def db_session(self) -> Session:
        return database.Session()

    @cached_property
    def current_user(self):
        user = self.identity.user
        if user is None:
            return
        user = self.db_session.merge(user)
        return user

    def permitted_for_current_user(self, obj: Any, permission: Permission) -> bool:
        return self.app._permits(self.identity, obj, permission)

    def q(self, *args, **kwargs) -> Query:
        return self.db_session.query(*args, **kwargs)

    def render_template(self, name: str, **context) -> str:
        with start_action(action_type="template-get", name=name):
            jinja_template: Template = self.app.jinja_env.get_template(name)
        try:
            with start_action(action_type="template-render", filename=jinja_template.filename):
                return jinja_template.render(**context)

        except Exception as e:
            raise RenderTemplateError(name, e) from e

    def flash(self, message, category="primary"):
        flashed_messages = self.browser_session.setdefault("flashed_messages", [])
        flashed_messages.append((category, message))

    @property
    def htmx(self):
        return self.headers.get("HX-Request")
