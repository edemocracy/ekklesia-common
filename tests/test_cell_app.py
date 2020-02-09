from ekklesia_common.cell import Cell
from ekklesia_common.cell_app import CellApp


class ATestModel:
    pass


class ATestApp(CellApp):
    pass


@ATestApp.cell(ATestModel, 'name')
class ATestCell(Cell):
    pass


def test_get_cell(request_for_cell):
    model = ATestModel()
    ATestApp.commit()
    app = ATestApp()
    assert app.get_cell(model, request_for_cell, 'name')
