from isis.main_window import Main_Window
from isis.widget import Widget
from isis.table_view import Table_View
from isis.data_model.table import Table
from PySide2.QtWidgets import QVBoxLayout
from dict import Dict as dict, List as list
from itzamara.remote import find_one_item
# agent_itzamara = Client('', 'itzamara')

from PySide2.QtWidgets import QComboBox
from PySide2.QtWidgets import QAbstractItemDelegate
from PySide2.QtWidgets import QStyledItemDelegate


class Column_Size_Item_Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 2:
            editor = QComboBox(parent)
            editor.addItems(['mini', 'small', 'normal', 'medium', 'large'])
            return editor


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        # self.columns.add('size', str)

        self.columns['sku'].changing_value = self.handle_changing_value_sku

        self.with_new_empty_row = True
        self.datasource = list()

    def handle_changing_value_sku(self, i, value):
        item = self.datasource[i]
        if value is not None and value:
            if 'sku' in item and item.sku == value:
                return False
            result = find_one_item(sku=value)
            if result is not None:
                item.sku = value
                item.description = result.description
            else:
                if 'sku' in item:
                    del item.sku
                    if 'description' in item:
                        del item.description
        elif 'sku' in item:
            del item.sku
            if 'description' in item:
                del item.description
        else:
            return False


class Print_Items_Price(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        cwidget = Widget(self)
        self.setWindowTitle('Imprimir precios de articulos')
        self.resize(500, 800)
        self.cwidget = cwidget
        self.tableview = Table_View(cwidget)
        self.tableview.setSelectionMode(Table_View.SingleSelection)
        self.tableview.setSelectionBehavior(Table_View.SelectItems)
        self.tableview.enable_delete_row_with_supr = True

        mainlayout = QVBoxLayout(cwidget)
        mainlayout.addWidget(self.tableview)
        cwidget.layout = mainlayout

        self.model = Items_Model()
        self.tableview.model = self.model
        # self.tableview.setItemDelegateForColumn(2, Column_Size_Item_Delegate())
        toolbar = self.addToolBar('file')
        action_print = toolbar.addAction('Imprimir')

        action_print.triggered.connect(self.print)

    def print(self):
        items = self.model.datasource
        for item in items:
            


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    v = Print_Items_Price()
    v.show()
    sys.exit(app.exec_())
