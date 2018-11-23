from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.menu import Menu
from PySide2.QtCore import Qt
from isis.main_window import Main_Window
from isis.widget import Widget
from sarah.acp_bson import Client
from itzamara import key_to_sort_item
from valentine import get_mass_literal
from isis.h_box_layout import H_Box_Layout

from isis.itzamara.create_item import Create_Item


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('unit_measure', str)
        self.columns.add('mass', str)
        self.columns.add('created', str)
        self.columns.add('modified', str)
        self.columns.add('pack', bool)
        self.columns.add('lifetime', str)
        self.datasource = list()
        self.readonly = True

        self.columns['mass'].getter_data = lambda x: get_mass_literal(x.mass) if 'mass' in x else None
        self.columns['unit_measure'].name = 'unit'


class Items_Table_View(Table_View):
    def mousePressEvent(self, event):
        Table_View.mousePressEvent(self, event)
        if event.button() == Qt.RightButton:
            menu = Menu(self)
            action_view = menu.addAction('view')
            action_edit = menu.addAction('edit')
            menu.popup(event.globalPos())


class Items(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(1000, 600)
        self.setWindowTitle('itzamara/items')
        self.cwidget = Widget(self)

        self.itemstable = Items_Table_View(self.cwidget)
        mainlayout = H_Box_Layout(self.cwidget)
        mainlayout.addWidget(self.itemstable)

        self.setLayout(mainlayout)
        self.itemsmodel = Items_Model()
        self.itemstable.model = self.itemsmodel

        self.agent_itzamara = Client('isis.itzamara.items', 'itzamara')
        msg = {'type_message': 'find', 'type': 'itzamara/item'}
        answer = self.agent_itzamara.send_msg(msg)
        answer.result.sort(key=key_to_sort_item)
        self.itemsmodel.datasource = answer.result

        toolbar = self.addToolBar('Item')
        action_create = toolbar.addAction('Create')
        action_create.triggered.connect(self.handle_action_item_create)

    def handle_action_item_create(self):
        dialog = Create_Item(self)
        dialog.show()

    @property
    def items(self):
        return self.itemsmodel.datasource

    @items.setter
    def items(self, x):
        self.itemsmodel.datasource = x


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Items()
    vv.show()
    sys.exit(app.exec_())
