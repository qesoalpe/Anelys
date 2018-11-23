from isis.main_window import Main_Window
from isis.push_button import Push_Button
from isis.v_box_layout import V_Box_Layout
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.itzamara.item_list import Item_List
from decimal import Decimal
from sarah.acp_bson import Client
from isis.widget import Widget


class Model_Inventory(Table):
    def __init__(self):
        Table.__init__(self, 'inventory')
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('inventory_absolut', Decimal, '#,##0.###')
        self.columns.add('updated', str)
        self.columns['inventory_absolut'].name = 'inventory'
        self.with_new_empty_row = False
        self.readonly = True


class Table_View_Inventory(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)


class Inventoring:
    def __init__(self, gui_parent=None):
        self.model = Model_Inventory()
        self.gui_parent = gui_parent
        self._tableview = Table_View_Inventory(self.gui_parent)
        self._tableview.setModel(self.model)
        # self.inventoring = list()
        self.model.datasource = list()

    def change_inventoring(self):
        item_list_manager = Item_List(self.gui_parent)
        item_list_manager.items = self.model.datasource
        item_list_manager.exec_()
        self.inventoring = item_list_manager.items

    @property
    def tableview(self):
        return self._tableview

    @tableview.setter
    def tableview(self, tableview):
        old_table = self._tableview
        self.tableview = tableview
        tableview.setModel(self.model)
        if old_table is not None:
            old_table.deleteLater()
            del old_table

    @property
    def inventoring(self):
        return self.model.datasource

    @inventoring.setter
    def inventoring(self, inventoring):
        agent_valentine = Client('inventory', 'valentine')
        from dict import Dict
        msg = Dict({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut',
                    'items': inventoring, 'projection': {'updated': True}})
        try:
            storage = self.storage
            if storage is not None:
                msg.storage = storage
        except:
            pass
        answer = agent_valentine(msg)
        self.model.datasource = answer['items']

    def storage_changed(self, storage):
        self.storage = storage
        agent_valentine = Client('inventory', 'valentine')
        from dict import Dict
        msg = Dict({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut',
                    'items': self.model.datasource})
        try:
            storage = self.storage
            if storage is not None:
                msg.storage = storage
        except:
            pass
        answer = agent_valentine(msg)
        self.model.datasource = answer['items']


class Inventory(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Inventory')
        self.resize(500, 600)

        self.cwidget = Widget(self)
        self.setCentralWidget(self.cwidget)

        self._inventoring = Inventoring(gui_parent=self.cwidget)
        from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
        self.widget_storage = Widget_Viewer_Storage(self.cwidget)
        self.tableview = self.inventoring.tableview

        btn_inventoring = Push_Button('inventoring', self.cwidget)
        self.widget_storage.with_button_change = True

        layout_main = V_Box_Layout(self.cwidget)
        layout_main.addWidget(self.widget_storage)
        layout_main.addWidget(self.tableview)
        layout_main.addWidget(btn_inventoring)
        self.cwidget.setLayout(layout_main)

        btn_inventoring.clicked.connect(self.inventoring.change_inventoring)
        self.widget_storage.storage_changed.suscribe(self.inventoring.storage_changed)

    @property
    def inventoring(self):
        return self._inventoring

    @inventoring.setter
    def inventoring(self, inventoring):
        if isinstance(inventoring, list):
            self._inventoring.inventoring = inventoring


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application()
    vv = Inventory()
    vv.show()
    sys.exit(app.exec_())
