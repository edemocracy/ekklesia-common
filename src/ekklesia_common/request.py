from functools import cached_property
from typing import Any
import morepath
from ekklesia_common import database
from ekklesia_common.permission import Permission
from jinja2 import Template
from sqlalchemy.orm import Session, Query



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

    def render_template(self, template: str, **context) -> str:
        jinja_template: Template = self.app.jinja_env.get_template(template)
        return jinja_template.render(**context)
