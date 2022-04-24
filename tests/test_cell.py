import inspect
from unittest.mock import Mock

from munch import Munch
from pytest import fixture, raises
from webob.request import BaseRequest

import ekklesia_common.cell
from ekklesia_common.app import make_jinja_env
from ekklesia_common.cell import (
    Cell,
    CellAttributeNotFound,
    JinjaCellContext,
    JinjaCellEnvironment,
)
from ekklesia_common.request import EkklesiaRequest


@fixture
def jinja_env(app):
    import jinja2

    template_loader = jinja2.loaders.PackageLoader("tests")
    return make_jinja_env(
        jinja_environment_class=JinjaCellEnvironment,
        jinja_options=dict(loader=template_loader),
        app=app,
    )


@fixture
def render_template(jinja_env):
    def render_template(template, **context):
        template = jinja_env.get_template(template)
        return template.render(**context)

    return render_template


@fixture
def cell_class(model):
    class DummyMarkup(str):
        def __init__(self, content):
            self.content = content

    _model = model

    class TestCell(Cell):
        model_properties = ["id", "title"]
        markup_class = DummyMarkup

        def _get_cell_class(self, model, view):
            return self.__class__

        def test_url(self):
            return "https://example.com/test"

        @Cell.fragment
        def alternate_fragment(self, **k):
            return self.render_template("alternate_template", **k)

        @Cell.fragment
        def fragment_without_params(self):
            pass

        cannot_call_this = None

        fragment_from_name = Cell.fragment("name")

    return TestCell


@fixture
def cell(cell_class, model, request_for_cell):
    cell_class.render_template = Mock()
    return cell_class(model, request_for_cell)


@fixture
def context(cell, jinja_env):
    parent = {"_cell": cell}
    return JinjaCellContext(jinja_env, parent, None, {}, {})


def test_root_cell_uses_layout(cell):
    assert cell.layout


def test_nested_cells(model, cell):
    parent = cell
    child = parent.cell(model)
    assert child.parent == parent
    assert not child.layout


def test_cell_cell(cell, model):
    another_cell = cell.cell(model)
    assert another_cell.__class__ == cell.__class__


def test_cell_getattr(cell, model):
    assert cell.id == model.id
    assert cell.title == model.title


def test_cell_automatic_property_from_no_arg_method(cell):
    assert cell.test_url == "https://example.com/test"


def test_cell_fragment_methods_are_not_properties(cell):
    # Fragment methods should not be turned into properties
    assert inspect.ismethod(cell.alternate_fragment)
    assert inspect.ismethod(cell.fragment_without_params)


def test_cell_fragment_method_has_marker(cell):
    assert cell.alternate_fragment._fragment


def test_fragment_from_name_with_prefix(cell):
    cell.template_prefix = "templates"
    cell.render_template = Mock()
    cell.fragment_from_name()
    cell.render_template.assert_called_with("templates/name.j2.jade")


def test_fragment_from_name_without_prefix(cell):
    cell.render_template = Mock()
    cell.fragment_from_name()
    cell.render_template.assert_called_with("name.j2.jade")


def test_cell_getitem(cell, model):
    assert cell["id"] == model.id
    assert cell["title"] == model.title
    assert cell["test_url"] == cell.test_url


def test_cell_contains(cell, model):
    assert "id" in cell
    assert "title" in cell
    assert "test_url" in cell


def test_cell_attrs_override_model_attrs(cell, model):
    cell.id = 42
    assert cell["id"] == 42


def test_cell_template_path(cell, model):
    assert cell.template_path == "test.j2.jade"


def test_cell_show(cell, model):
    cell.show()
    cell.render_template.assert_called_with(cell.template_path)


def test_cell_render_cell(cell, model):
    cell.render_cell(model)
    cell.render_template.assert_called
    assert cell.render_template.call_args[0][0] == cell.template_path


def test_cell_render_cell_shows_error_if_view_method_not_callable(cell, model):
    with raises(ValueError) as e:
        cell.render_cell(model, "cannot_call_this")

    assert "cannot_call_this" in str(e)
    assert "TestModel" in str(e)


def test_cell_render_cell_fragment(cell, model):
    cell.render_cell(model, "alternate_fragment", some_option=42)
    cell.render_template.assert_called
    assert cell.render_template.call_args[0][0] == "alternate_template"


def test_cell_render_cell_collection(cell, model):
    model2 = model.copy()
    model2.title = "test2"
    models = [model, model2]
    cell.cell = Mock()
    cell.cell.return_value.show = Mock(return_value="test")
    result = cell.render_cell(collection=models, separator="&", some_option=42)
    assert result == "test&test"
    cell.cell.assert_any_call(model, layout=None, some_option=42)
    cell.cell.assert_any_call(model2, layout=None, some_option=42)


def test_cell_render_cell_collection_view_method_not_callable(cell, model):
    model2 = model.copy()
    model2.title = "test2"
    models = [model, model2]
    with raises(ValueError) as e:
        cell.render_cell(collection=models, view_name="cannot_call_this")

    assert "cannot_call_this" in str(e)
    assert "TestModel" in str(e)


def test_cell_render_cell_model_and_collection_not_allowed(cell, model):
    with raises(ValueError):
        cell.render_cell(model, collection=[], some_option=42)


def test_cell_jinja_integration(cell_class, model, render_template, request_for_cell):
    request_for_cell.render_template = render_template
    cell = cell_class(model, request_for_cell)
    res = cell.show()
    assert str(model.id) in res.content
    assert model.title in res.content


def test_context_resolve_or_missing(context):
    result = context.resolve_or_missing("title")
    assert result == "test"


def test_context_resolve_or_missing_raises_exception_for_inexistent(context):
    with raises(CellAttributeNotFound) as excinfo:
        context.resolve_or_missing("does_not_exist")

    assert "does_not_exist" in str(excinfo.value)


def test_context_resolve_or_missing_raises_exception_for_private(context):
    with raises(CellAttributeNotFound) as excinfo:
        context.resolve_or_missing("private")

    assert "private" in str(excinfo.value)
