from isis.dialog import Dialog
from isis.data_model.table import Table
from isis.table_view import Table_View
from decimal import Decimal as D
from isis.v_box_layout import V_Box_Layout
from isis.line_edit_command import Line_Edit_Command
from isis.itzamara.search_item import Search_Item
from utils import find_one
from PySide2.QtWidgets import QInputDialog
from perla.prices import get_last_purchase_price


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', D, 'c')
        self.columns.add('amount', D, 'c')
        self.datasource = list()


class Items_Table_View(Table_View):
    pass


class Returns(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 500)
        self.window_title = 'Devoluciones'

        self.table = Items_Table_View(self)
        self.txt_cmd = Line_Edit_Command(self)
        layout_main = V_Box_Layout(self)
        layout_main.addWidget(self.table)
        layout_main.addWidget(self.txt_cmd)
        self.layout = layout_main
        self.txt_cmd.command.suscribe(self.handle_cmd)

        self.model = Items_Model()
        self.table.model = self.model

    @property
    def items(self):
        return self.model.datasource

    def handle_cmd(self, cmd):
        searcher = Search_Item(self)
        searcher.search_by_sku = True
        searcher.search_by_code_ref = True
        result = searcher.search(cmd)
        if result is not None:
            r = find_one(lambda x: x.sku == result.sku, self.items)
            if r is not None:
                r.quanty += 1
                self.model.notify_row_changed(r)
            else:
                result.quanty = QInputDialog.getDouble(self, 'Cantidad', 'Ingresa la cantidad', 1, 0, 2)
                last_purchase_price = get_last_purchase_price(result)