from PySide.QtCore import *
from PySide.QtGui import *
from isis.itzamara.search_item import Search_Item
from isis.valentine.search_storage import Search_Storage
from sarah.acp_bson import Client
from copy import deepcopy
from isodate import datetime_isoformat
from datetime import datetime
from isis.data_model.table import Table
from decimal import Decimal
from utils import remove_values_none
from isis.utils import parse_number
from isis.table_view import Table_View
from isis.label import Label
from isis.line_edit import Line_Edit

# class Model_Items(QAbstractTableModel):
#     def __init__(self, parent):
#         QAbstractTableModel.__init__(self, parent)
#         self.agent_itzamara = Client('Create_Production', 'itzamara')
#
#     @property
#     def datasource(self):
#         return self._datasource
#
#     @datasource.setter
#     def datasource(self, x):
#         self._datasource = x
#         self.modelReset.emit()
#
#     def rowCount(self, parent=None):
#         if self._datasource is not None:
#             return len(self._datasource)
#         else:
#             return 0
#
#     def columnCount(self, parent=None):
#         return 3
#
#     def headerData(self, section, orientation, role):
#         if role == Qt.DisplayRole and orientation == Qt.Horizontal:
#             if section == self.COLUMN_SKU:
#                 return 'sku'
#             elif section == self.COLUMN_QUANTY:
#                 return 'quanty'
#             elif section == self.COLUMN_DESCRIPTION:
#                 return 'description'
#
#     def data(self, index, role):
#         if role == Qt.DisplayRole or role == Qt.EditRole:
#             data = self._datasource[index.row()]
#             if index.column() == self.COLUMN_SKU:
#                 if 'sku' in data:
#                     return data['sku']
#             elif index.column() == self.COLUMN_QUANTY:
#                 if 'quanty' in data:
#                     return format_decimal(data['quanty'], locale='es_mx')
#             elif index.column() == self.COLUMN_DESCRIPTION:
#                 if 'description' in data:
#                     return data['description']
#
#     def item_updated(self, index):
#         topleft = self.index(index, 0, QModelIndex())
#         bottomright = self.index(index, self.columnCount() - 1 if self.columnCount() > 0 else 0)
#         self.dataChanged.emit(topleft, bottomright)
#         if not self.contains_empty_items():
#             self.insert_item()
#
#     def setData(self, index, value, role):
#         if role == Qt.EditRole:
#             if index.column() == self.COLUMN_SKU:
#                 msg = {'type_message': 'find_one', 'type': 'itzamara/item',
#                        'query': {'sku': value}}
#                 answer = self.agent_itzamara(msg)
#                 if 'result' in answer and answer['result'] is not None:
#                     result = answer['result']
#                     data = self.datasource[index.row()]
#                     if 'sku' in result:
#                         data['sku'] = result['sku']
#                     elif 'sku' in data:
#                         del data['sku']
#
#                     if 'description' in result:
#                         data['description'] = result['description']
#                     elif 'description' in data:
#                         del data['description']
#
#                     if 'type' in result:
#                         data['type'] = result['type']
#                     elif 'type' in data:
#                         del data['type']
#                     self.item_updated(index.row())
#                 else:
#                     QMessageBox.warning(None, 'not found', 'item not found')
#                 return True
#             elif index.column() == self.COLUMN_QUANTY:
#                 data = self.datasource[index.row()]
#                 if value:
#                     data['quanty'] = parse_decimal(value, locale='es_mx')
#                 elif 'quanty' in data:
#                     del data['quanty']
#                 self.item_updated(index.row())
#                 return True
#             elif index.column() == self.COLUMN_DESCRIPTION:
#                 data = self.datasource[index.row()]
#                 searcher = Search_Item(None)
#                 result = searcher.search(value)
#                 if result is not None:
#                     if 'sku' in result:
#                         data['sku'] = result['sku']
#                     elif 'sku' in data:
#                         del data['sku']
#                     if 'description' in result:
#                         data['description'] = result['description']
#                     elif 'description' in data:
#                         del data['description']
#
#                     if 'type' in result:
#                         data['type'] = result['type']
#                     elif 'type' in data:
#                         del data['type']
#                 else:
#                     if 'sku' in data:
#                         del data['sku']
#                     if 'description' in data:
#                         del data['description']
#                     if 'type' in data:
#                         del data['type']
#                 self.item_updated(index.row())
#                 return True
#         return False
#
#     def contains_empty_items(self):
#         for data in self.datasource:
#             if 'description' not in data:
#                 return True
#         else:
#             return False
#
#     def insert_item(self, i=None, x=None):
#         if x is None:
#             x = dict()
#         if i is None:
#             i = len(self.datasource)
#         self.beginInsertRows(QModelIndex(), i, i)
#         self.datasource.insert(i, x)
#         self.endInsertRows()
#
#     def flags(self, index):
#         return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
#
#     COLUMN_SKU = 0
#     COLUMN_QUANTY = 1
#     COLUMN_DESCRIPTION = 2

agent_valentine = Client('', 'valentine')


def get_inventory(item, storage):
    try:
        answer = agent_valentine({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut',
                                  'item': item, 'storage': storage})
        if 'item' in answer and 'inventory_absolut' in answer.item and answer.item.inventory_absolut is not None:
            return answer.item.inventory_absolut
    except:
        return None


class Consumed_Model_Table(Table):
    def __init__(self, parent=None):
        Table.__init__(self, 'Consumed')
        self.columns.add('sku', str)
        self.columns.add('quanty', Decimal)
        self.columns.add('description', str)
        self.columns.add('inventory', Decimal, '0,###.###')

        self.columns['sku'].changing_value = self.handle_changing_sku
        self.columns['quanty'].changing_value = self.handle_changing_quanty
        self.columns['description'].changing_value = self.handle_changing_description
        self.with_new_empty_row = True
        self.parentgui = None
        self.storage = None

    def set_storage(self, storage):
        self.storage = storage

    def handle_changing_sku(self, index, value):
        from itzamara.rpc import find_one_item
        item = find_one_item({'sku': value})
        data = self.datasource[index]
        if item is not None:
            data['sku'] = item['sku'] if 'sku' in item else None
            data['description'] = item['description'] if 'description' in item else None
            data['type'] = item['type'] if 'type' in item else None
            data.inventory = get_inventory(item, self.storage)
            remove_values_none(data)
        else:
            QMessageBox.warning(self, 'error', 'item not found')
            if 'sku' in data: del data['sku']
            if 'description' in data: del data['description']
            if 'type' in data: del data['type']
            if 'inventory' in data: del data.inventory

    def handle_changing_quanty(self, index, value):
        data = self.datasource[index]
        if value is not None:
            if isinstance(value, Decimal):
                data['quanty'] = value
            elif isinstance(value, str):
                data['quanty'] = parse_number(value)
            else:
                raise Exception()
        else:
            if 'quanty' in data: del data['quanty']

    def handle_changing_description(self, index, value):
        searcher = Search_Item(self.parentgui)
        result = searcher.search(value)
        data = self.datasource[index]
        if result is not None:
            data['sku'] = result['sku'] if 'sku' in result else None
            data['description'] = result['description'] if 'description' in result else None
            data['type'] = result['type'] if 'type' in result else None
            data.inventory = get_inventory(result, self.storage)
            remove_values_none(data)
        else:
            if 'sku' in data: del data['sku']
            if 'description' in data: del data['description']
            if 'type' in data: del data['type']

Model_Items = Consumed_Model_Table


class Table_View_Items(Table_View):
    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectItems)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            index = self.currentIndex()

            if index.isValid() and not self.model.is_the_new_empty_row(index.row()):
                r = QMessageBox.question(self, 'remover', 'Desea remover el articulo?', QMessageBox.Yes | QMessageBox.No)
                if r == QMessageBox.Yes:
                    self.model.remove_data(index.row())
        Table_View.keyPressEvent(self, event)


class Create_Production(QMainWindow):
    def __init__(self):
        from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
        QMainWindow.__init__(self)
        self.setWindowTitle('Create_Production')
        self.resize(800, 500)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        self.viewerstorage = Widget_Viewer_Storage(self.cwidget)
        self.viewerstorage.with_button_change = True

        self.tableconsumed = Table_View_Items(self.cwidget)
        self.tableproduced = Table_View_Items(self.cwidget)

        self.modelconsumed = Model_Items()
        self.modelproduced = Model_Items()
        self.modelconsumed.parentgui = self
        self.modelproduced.parentgui = self

        self._consumed = list()
        self._produced = list()

        self.modelconsumed.datasource = self._consumed
        self.modelproduced.datasource = self._produced

        self.tableconsumed.model = self.modelconsumed
        self.tableproduced.model = self.modelproduced

        lbl_table_consumed = QLabel('consumed', self.cwidget)
        lbl_table_produced = QLabel('produced', self.cwidget)

        lbl_by = Label('por: ', self.cwidget)
        lbl_by_name = Label('name: ', self.cwidget)
        self.txt_by_name = Line_Edit(self.cwidget)
        lbl_by.fix_size_based_on_font()
        #self.txt_by_name.setFixedWidth(self.txt_by_name.fontMetrics().width('1234567890123456789012345678901234567890'))

        layoutmain = QVBoxLayout(self.cwidget)
        layoutcurrent = QHBoxLayout()
        layoutcurrent.addWidget(self.viewerstorage)
        layoutcurrent.addWidget(lbl_by_name)
        layoutcurrent.addWidget(self.txt_by_name)
        layoutmain.addLayout(layoutcurrent)
        tableslayout = QGridLayout()
        tableslayout.addWidget(lbl_table_consumed, 0, 0)
        tableslayout.addWidget(lbl_table_produced, 0, 1)
        tableslayout.addWidget(self.tableconsumed, 1, 0)
        tableslayout.addWidget(self.tableproduced, 1, 1)
        layoutmain.addLayout(tableslayout)
        self.cwidget.setLayout(layoutmain)

        file_toolbar = self.addToolBar('file')
        action_create = file_toolbar.addAction('create')

        action_create.triggered.connect(self.create)
        self.viewerstorage.storage_changed.suscribe(self.modelconsumed.set_storage)
        self.viewerstorage.storage_changed.suscribe(self.modelproduced.set_storage)

        self.agent_donell = Client('Create_Production', 'donell')

    @property
    def consumed(self):
        x = deepcopy(self._consumed)
        for d in x[:]:
            if 'sku' not in d:
                x.remove(d)
            if 'inventory' in d:
                del d.inventory
        return x

    @property
    def produced(self):
        x = deepcopy(self._produced)
        for d in x[:]:
            if 'sku' not in d:
                x.remove(d)
            if 'inventory' in d:
                del d.inventory
        return x

    @property
    def production(self):
        production = {'consumed': self.consumed, 'produced': self.produced}
        return production

    @property
    def storage(self):
        return self.viewerstorage.storage

    @storage.setter
    def storage(self, x):
        self.viewerstorage.storage = x

    def create(self):
        production = {'consumed': self.consumed, 'produced': self.produced, 'storage': self.storage}
        if production['consumed'] is None:
            QMessageBox.warning(self, 'error', 'consumed should not be None')
            return
        if production['produced'] is None:
            QMessageBox.warning(self, 'error', 'produced should not be None')
            return
        if production['storage'] is None:
            QMessageBox.warning(self, 'error', 'storage should not be None')
            return
        production['datetime'] = datetime_isoformat(datetime.now())
        msg = {'type_message': 'action', 'action': 'donell/create_production', 'production': production,
               'datetime': datetime_isoformat(datetime.now()), }
        answer = self.agent_donell(msg)
        if 'error' in answer and answer['error']:
            QMessageBox.warning(self, 'error', 'an error has happened')
        else:
            QMessageBox.information(self, 'success', 'production created successfully')
            self.close()


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Create_Production()
    vv.show()
    sys.exit(app.exec_())
