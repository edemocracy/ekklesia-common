from ekklesia_common.app import App

class Index:
    pass


@App.path(model=Index,  path='')
def index():
    return Index()


@App.html(model=Index)
def show(self, request):
    from ..cell.index import IndexCell
    return IndexCell(self, request).show()
