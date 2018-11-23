from isis.dialog import Dialog
from isis.data_model.table import Table
from isis.table_view import Table_View
from decimal import Decimal
from PySide.QtGui import QVBoxLayout


class Items_For_Receive(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 500)
        self.setWindowTitle(self.__class__.__name__)
        self.tableview = Table_View(self)
        self.model = Table()
        self.model.columns.add('sku', str)
        self.model.columns.add('quanty', Decimal, '#,##0.###')
        self.model.columns.add('description', str)
        self.model.readonly = True
        self.tableview.model = self.model
        layout_main = QVBoxLayout(self)
        layout_main.addWidget(self.tableview)
        self.setLayout(layout_main)

        from katherine import d1
        c = d1.bethesda.order.find({'status': {'$in': ['to_receive', 'for_receive']}}, {'_id': False})
        from utils import find_one
        items = list()
        for order in c:
            if 'items' in order:
                for item in order['items']:
                    from copy import deepcopy
                    if 'sku' in item:
                        i = find_one(lambda x: x.sku == item.sku, list(filter(lambda x: 'sku' in x, items)))
                        if i is not None:
                            i.quanty = item.quanty + i.quanty if 'quanty' in i else item.quanty
                        else:
                            i = deepcopy(item)
                            for k in list(i.keys()):
                                if k not in ['sku', 'quanty', 'description']:
                                    del i[k]
                            items.append(i)
                    else:
                        items.append(deepcopy(item))

        from sorter import Sorter
        sorter = Sorter()
        sorter.columns.add('description', 1)
        sorter.sort(items)
        self.model.datasource = items


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Items_For_Receive()
    vv.show()
    sys.exit(app.exec_())
