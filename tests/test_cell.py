import inspect
from unittest.mock import Mock
from munch import Munch
from pytest import fixture, raises
import ekklesia_common.cell
from ekklesia_common.cell import Cell, JinjaCellEnvironment
from ekklesia_common.app import make_jinja_env
from ekklesia_common.request import EkklesiaRequest
from webob.request import BaseRequest


@fixture
def model():
    class TestModel(Munch):
        pass

    return TestModel(id=5, title="test", private="secret")


@fixture
def request_for_cell(app):
    environ = BaseRequest.blank('test').environ
    m = Mock(spec=EkklesiaRequest(environ, app))
    m.i18n = Mock()
    return m


@fixture
def jinja_env(app):
    import jinja2
    template_loader = jinja2.loaders.PackageLoader("tests")
    return make_jinja_env(jinja_environment_class=JinjaCellEnvironment, jinja_options=dict(loader=template_loader), app=app)


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
        model = _model.__class__
        model_properties = ['id', 'title']
        markup_class = DummyMarkup

        def test_url(self):
            return "https://example.com/test"

        @Cell.fragment
        def alternate_fragment(self, **k):
            return self.render_template('alternate_template', **k)

        @Cell.fragment
        def fragment_without_params(self):
            pass

    return TestCell


@fixture
def cell(cell_class, model, request_for_cell):
    return cell_class(model, request_for_cell)


def test_root_cell_uses_layout(cell):
    assert cell.layout


def test_nested_cells(model, cell):
    parent = cell
    child = parent.cell(model)
    assert child.parent == parent
    assert not child.layout


def test_cell_is_registrated(cell, model):
    assert model.__class__ in ekklesia_common.cell._cell_registry


def test_cell_cell(cell, model):
    another_cell = cell.cell(model)
    assert another_cell.__class__ == cell.__class__


def test_cell_getattr(cell, model):
    assert cell.id == model.id
    assert cell.title == model.title


def test_cell_automatic_properties(cell):
    assert cell.test_url == 'https://example.com/test'
    assert inspect.ismethod(cell.alternate_fragment)
    assert inspect.ismethod(cell.fragment_without_params)


def test_cell_fragment_methods(cell):
    assert cell.alternate_fragment._fragment


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


def test_cannot_access_private_attr_from_cell(cell, model):
    with raises(AttributeError):
        cell.private


def test_missing_cell_attribute_raises_exception(cell, model):
    with raises(AttributeError) as excinfo:
        cell.does_not_exist

    assert 'does_not_exist' in str(excinfo.value)


def test_missing_cell_item_raises_exception(cell, model):
    with raises(KeyError) as excinfo:
        cell['does_not_exist']

    assert 'does_not_exist' in str(excinfo.value)


def test_cell_template_path(cell, model):
    assert cell.template_path == "test.j2.jade"


def test_cell_show(cell, model):
    cell.render_template = Mock()
    cell.show()
    cell.render_template.assert_called_with(cell.template_path)


def test_cell_render_cell(cell, model, request_for_cell):
    cell.render_cell(model)
    request_for_cell.render_template.assert_called
    assert request_for_cell.render_template.call_args[0][0] == cell.template_path


def test_cell_render_cell_fragment(cell, model, request_for_cell):
    cell.render_cell(model, 'alternate_fragment', some_option=42)
    request_for_cell.render_template.assert_called
    assert request_for_cell.render_template.call_args[0][0] == 'alternate_template'


def test_cell_render_cell_collection(cell, model):
    model2 = model.copy()
    model2.title = "test2"
    models = [model, model2]
    cell.cell = Mock(cell)
    cell.cell.return_value.show = Mock(return_value='test')
    result = cell.render_cell(collection=models, separator='&', some_option=42)
    assert result == 'test&test'
    cell.cell.assert_any_call(model, layout=None, some_option=42)
    cell.cell.assert_any_call(model2, layout=None, some_option=42)


def test_cell_render_cell_model_and_collection_not_allowed(cell, model):
    with raises(ValueError):
        cell.render_cell(model, collection=[], some_option=42)


def test_cell_jinja_integration(cell, model, render_template, request_for_cell):

    request_for_cell.render_template.side_effect = render_template
    res = cell.show()
    assert str(model.id) in res.content
    assert model.title in res.content
