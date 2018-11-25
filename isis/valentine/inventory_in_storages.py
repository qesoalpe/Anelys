from isis.dialog import Dialog
from isis.v_box_layout import V_Box_Layout
from isis.table_view import Table_View
from isis.data_model.table import Table
from isis.label import Label
from isis.grid_layout import Grid_Layout
from decimal import Decimal as D


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('storage', str)
        self.columns.add('type', str)
        self.columns.add('inventory', D, '#,##0.###')
        self.datasource = list()
        self.readonly = True
        self.columns['storage'].getter_data = lambda x: x.storage.name if 'storage' in x and 'name' in x.storage else None


class Inventory_In_Storages(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(250, 400)
        self.window_title = 'Inventario en almacenes'
        self.close_with_escape = True

        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)

        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()

        self.lbl_sku = Label(self)
        self.lbl_description = Label(self)

        self.table = Table_View(self)

        layout_main = V_Box_Layout(self)
        layout_item = Grid_Layout()
        layout_item.addWidget(lbl_sku, 0, 0)
        layout_item.addWidget(self.lbl_sku, 0, 1)
        layout_item.addWidget(lbl_description, 1, 0)
        layout_item.addWidget(self.lbl_description, 1, 1)
        layout_main.addLayout(layout_item)
        layout_main.addWidget(self.table)
        self.layout = layout_main

        self.model = Items_Model()
        self.table.model = self.model

    @property
    def item(self):
        return self._item
    
    @item.setter
    def item(self, item):
        if item is None:
            self.lbl_sku.text = None
            self.lbl_description.text = None
            self.model.datasource = list()
        else:
            self.lbl_sku.text = item.sku if 'sku' in item else None
            self.lbl_description.text = item.description if 'description' in item else None
            if 'inventory' in item:
                self.model.datasource = item.inventory
            else:
                self.model.datasource = list()

    @property
    def inventory(self):
        return self.model.datasource
