from isis.data_model.table import Table
from utils import find_one


class filter_after_searching:
    def __init__(self, itemsrepository):
        self.itemsrepository = itemsrepository

    def __call__(self, e):
        if 'selected' in e:
            i = find_one(lambda x: x.sku == e.selected.sku, self.itemsrepository)
            if i is not None:
                e.selected = i
            else:
                del e.selected
                e.table = Table()
                e.list = list()

        if 'table' in e and 'list' in e:
            for item in e.list[:]:
                if find_one(lambda x: x.sku == item.sku, self.itemsrepository) is None:
                    e.list.remove(item)

            e.table.modelReset.emit()
