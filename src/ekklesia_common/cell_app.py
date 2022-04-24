from typing import get_type_hints

import dectate
import morepath
import reg
from morepath.directive import (
    PredicateAction,
    SettingAction,
    isbaseclass,
    issubclass_or_none,
)


class CellAction(dectate.Action):

    depends = [SettingAction, PredicateAction]

    filter_convert = {
        "model": dectate.convert_dotted_name,
        "render": dectate.convert_dotted_name,
        "permission": dectate.convert_dotted_name,
    }

    filter_compare = {"model": isbaseclass, "permission": issubclass_or_none}

    app_class_arg = True

    def __init__(self, model=None, name="", permission=None, **predicates):
        self.model = model
        self.name = name
        self.permission = permission
        self.predicates = predicates

    def key_dict(self):
        """Return a dict containing cell registration info,
        for instance model, etc."""
        result = self.predicates.copy()
        result["model"] = self.model
        result["name"] = self.name
        return result

    def identifier(self, app_class):
        return app_class.get_cell_class.by_predicates(**self.key_dict()).key

    def perform(self, obj, app_class):
        def get_cell_class(self, model, name):
            return obj

        def cell_view(self, request):
            cell = obj(self, request)
            return cell.show()

        if self.model is None:
            self.model = get_type_hints(obj)["_model"]

        obj.model = self.model
        app_class.get_cell_class.register(get_cell_class, **self.key_dict())
        app_class.html(cell_view)


class CellApp(morepath.App):

    cell = dectate.directive(CellAction)

    @morepath.dispatch_method(reg.match_instance("model"), reg.match_key("name"))
    def get_cell_class(self, model, name):
        return None

    def get_cell(self, model, request, name):
        return self.get_cell_class(model, name)(model, request)
