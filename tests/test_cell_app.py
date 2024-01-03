from ekklesia_common.cell import Cell
from ekklesia_common.cell_app import CellApp
from tests.fixtures import ATestModel


class ATestApp(CellApp):
    pass


@ATestApp.cell("name")
class ATestCell(Cell):

    _model: ATestModel


def test_get_cell(request_for_cell):
    model = ATestModel()
    ATestApp.commit()
    app = ATestApp()
    assert app.get_cell(model, request_for_cell, "name")
