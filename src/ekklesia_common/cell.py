from __future__ import annotations

import inspect
import os.path
from functools import cached_property
from typing import Any, ClassVar, Dict, Iterable, Type

import case_conversion
import jinja2
import jinja2.utils
from markupsafe import Markup
from webob import Request

_cell_registry: Dict[Any, "Cell"] = {}


def find_cell_by_model_instance(model) -> "Cell":
    return _cell_registry[model.__class__]


class CellMeta(type):
    """
    Registers Cell types that are bound to a Model class.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        model = getattr(cls, "model", None)
        if model:
            _cell_registry[model] = cls
        if "template_prefix" not in cls.__dict__:
            module_path = cls.__module__.split(".")
            if module_path[1] == "concepts":
                cls.template_prefix = module_path[2]
            else:
                cls.template_prefix = None

        return super().__init__(name, bases, attrs)

    def __new__(meta, name, bases, dct):
        # only for subclasses, not for Cell class
        if bases:
            for k, v in dct.items():
                if (
                    not k.startswith("_")
                    and inspect.isfunction(v)
                    and not hasattr(v, "_fragment")
                    and len(inspect.signature(v).parameters) == 1
                ):
                    # turn functions with single argument (self) into cached properties
                    dct[k] = cached_property(v)

        return super().__new__(meta, name, bases, dct)


class CellAttributeAccessError(Exception):
    def __init__(self, cell, attribute_name, exception) -> None:
        cell_type = type(cell).__name__
        self.cell_type = cell_type
        self.attribute_name = attribute_name
        msg = f"{cell_type}.{attribute_name} raised {type(exception).__name__}: {exception}"
        super().__init__(msg)


class CellAttributeNotFound(Exception):
    def __init__(self, cell, attribute_name) -> None:
        cell_type = type(cell).__name__
        self.cell_type = cell_type
        self.attribute_name = attribute_name
        msg = (
            f"{cell_type} has no attribute '{attribute_name}'. "
            + "Is it from the model? Did you forget to add it to 'model_properties'?"
        )
        super().__init__(msg)


class Cell(metaclass=CellMeta):
    """
    View model base class which is basically a wrapper around a template.
    Templates can access attributes of the cell and some selected model properties directly.
    """

    model: ClassVar[Any]
    model_properties: Iterable[str] = []
    layout = True
    template_prefix: ClassVar[str]
    #: class that should be used to mark safe HTML output. Must be a subclass of str.
    markup_class: Type[str] = Markup

    def __init__(
        self,
        model,
        request: Request,
        collection: Iterable = None,
        layout: bool = None,
        parent: "Cell" = None,
        template_path: str = None,
        **options,
    ) -> None:
        """ """
        self._model = model
        self._request = request
        self.current_user = request.current_user
        self._app = request.app
        self._s = request.app.settings
        self._ = request.i18n.gettext
        self.parent = parent
        self.collection = collection
        self._template_path = template_path
        self.options = options
        # if no parent is set, the layout is enabled by default. This can be overriden by the `layout` arg
        if layout is not None:
            self.layout = layout
        elif parent is None:
            self.layout = True
        else:
            self.layout = False

    @property
    def template_path(self) -> str:
        if self._template_path is None:
            cell_name = self.__class__.__name__
            if not cell_name.endswith("Cell"):
                raise Exception(
                    "Cell name does not end with Cell, you must override template_path!"
                )

            name = case_conversion.snakecase(cell_name[: -len("Cell")])

            if self.template_prefix is not None:
                self._template_path = f"{self.template_prefix}/{name}.j2.jade"
            else:
                self._template_path = f"{name}.j2.jade"

        return self._template_path

    def render_template(self, template_path) -> str:
        return self.markup_class(
            self._request.render_template(template_path, _cell=self)
        )

    def show(self):
        return self.render_template(self.template_path)

    # template helpers

    def link(self, model, name="", *args, **kwargs) -> str:
        return self._request.link(model, name, *args, **kwargs)

    def class_link(
        self, model_class, variables: Dict[str, Any], name="", *args, **kwargs
    ) -> str:
        return self._request.class_link(model_class, variables, name, *args, **kwargs)

    def static_url(self, path):
        return os.path.join(self._s.static_files.base_url, path)

    def _get_cell_class(self, model, view_name):
        # multiple new-style cells can be registered for a model class
        cell_class = self._app.get_cell_class(model, view_name)
        # look up old-style cells (only one per model class)
        if cell_class is None:
            cell_class = find_cell_by_model_instance(model)

        return cell_class

    def cell(self, model, layout: bool = None, view_name="", **options) -> "Cell":
        """Look up a cell by model and create an instance.
        The parent cell is set to self which also means that it will be rendered without layout by default.
        """
        cell_class = self._get_cell_class(model, view_name)
        return cell_class(
            model=model, request=self._request, layout=layout, parent=self, **options
        )

    def render_cell(
        self,
        model=None,
        view_name: str = None,
        collection: Iterable = None,
        separator: str = None,
        layout: bool = None,
        **options,
    ) -> str:
        """Look up a cell by model and render it to HTML.
        The parent cell is set to self which also means that it will be rendered without layout by default.
        """
        view_method_name = view_name if view_name is not None else "show"
        if collection is not None:
            if model is not None:
                raise ValueError(
                    "model and collection arguments cannot be used together!"
                )

            parts = []

            for item in collection:
                view_method = getattr(
                    self.cell(item, layout=layout, **options), view_method_name
                )

                if not callable(view_method):
                    raise ValueError(
                        f"view method '{view_method_name}' of {item} is not callable, it is: {view_method}"
                    )

                parts.append(view_method())

            if separator is None:
                separator = "\n"

            return self.markup_class(separator.join(parts))

        else:
            view_method = getattr(
                self.cell(model, layout=layout, **options), view_method_name
            )
            if not callable(view_method):
                raise ValueError(
                    f"view method '{view_method_name}' of {model} is not callable, it is: {view_method}"
                )
            return view_method()

    @classmethod
    def fragment(cls, func_or_name):
        """Decorator for cell methods that provide additional HTML.
        This can be used for template fragmentation or alternative presentation
        of the same concept.
        Can be called with a string argument as a shortcut for creating a
        fragment method based on conventions:

        `fragment = Cell.fragment('name')`
        creates a method that renders the template `{template_prefix}/name.j2.jade`
        """
        if callable(func_or_name):
            func = func_or_name
            func._fragment = True
            return func
        else:
            name = func_or_name

            def fragment_method(self):
                if self.template_prefix is not None:
                    template = f"{self.template_prefix}/{name}.j2.jade"
                else:
                    template = f"{name}.j2.jade"
                return self.render_template(template)

            fragment_method._fragment = True
            fragment_method.__name__ = name
            return fragment_method

    @classmethod
    def template_fragment(cls, template_name: str):
        """This can be used for template fragmentation or alternative presentation
        of the same concept.
        Can be called with a string argument as a shortcut for creating a
        fragment method based on conventions:

        `fragment = Cell.template_fragment('name')`
        creates a method that renders the template `{template_prefix}/name.j2.jade`
        """

        def fragment_method(self) -> str:
            if self.template_prefix is not None:
                template = f"{self.template_prefix}/{template_name}.j2.jade"
            else:
                template = f"{name}.j2.jade"
            return self.render_template(template)

        fragment_method._fragment = True
        fragment_method.__name__ = template_name
        return fragment_method

    @cached_property
    def self_link(self) -> str:
        return self.link(self._model)

    @cached_property
    def self_url(self) -> str:
        return self.link(self._model)

    def self_view_url(self, view_name):
        return self.link(self._model, view_name)

    @cached_property
    def edit_url(self) -> str:
        return self.link(self._model, "+edit")

    @cached_property
    def new_url(self) -> str:
        return self.link(self._model, "+new")

    # magic starts here...

    def __getattribute__(self, name):
        """ """
        try:
            ret = object.__getattribute__(self, name)
        except Exception as e:
            if isinstance(e, AttributeError) and not hasattr(self.__class__, name):
                # We got a AttributeError here that tells us that the class doesn't
                # have a member called `name`. raising it now causes __getattr__
                # to be called next.
                raise

            # AttributeErrors from the called attribute are converted so they don't
            # trigger __getattr__ and produce a misleading error.
            raise CellAttributeAccessError(self, name, e) from e

        return ret

    def __getattr__(self, name):
        if name in self.model_properties:
            return getattr(self._model, name)

        raise AttributeError()

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as e:
            # standard __getitem__ raises an KeyError, let's do the same
            raise KeyError(str(e))

    def __contains__(self, name):
        return name in self.model_properties or hasattr(self, name)


class JinjaCellContext(jinja2.runtime.Context):
    """
    Custom jinja context with the ability to look up template variables in a cell (view model)
    """

    def __init__(self, environment, parent, name, blocks, globals):
        super().__init__(environment, parent, name, blocks, globals)
        self._cell = parent.get("_cell")

    def resolve_or_missing(self, key):
        resolved = super().resolve_or_missing(key)

        if self._cell is not None:
            cell = self._cell
            if key == "_request":
                return cell._request

            if key in cell:
                return cell[key]

            if resolved == jinja2.utils.missing:
                raise CellAttributeNotFound(cell, key)

        return resolved

    def __contains__(self, name):
        if self._cell and name in self._cell:
            return True

        return super().__contains__(name)


class JinjaCellEnvironment(jinja2.Environment):
    """
    Example jinja environment class which uses the JinjaCellContext
    """

    context_class = JinjaCellContext
