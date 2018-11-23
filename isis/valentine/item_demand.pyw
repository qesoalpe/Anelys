from PySide.QtCore import *
from PySide.QtGui import *
from isis.valentine.search_storage import Search_Storage
from isis.itzamara.search_item import Search_Item
from sarah.acp_bson import Client

COLUMN_ITEM_SKU = 0
COLUMN_ITEM_DESCRIPTION = 1
COLUMN_PERIOD = 2
COLUMN_DEMAND = 3


class Delegate_Integer(QStyledItemDelegate):
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setButtonSymbols(QSpinBox.NoButtons)
        editor.setMaximum(100000000)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value is None:
            editor.setValue(0)
        else:
            editor.setValue(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class Table_Model_Items_Demand(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = list()
        self.handler_changing_item_sku = None
        self.handler_changing_item_description = None
        self.handler_changing_period = None
        self.handler_changing_demand = None

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def rowCount(self, parent):
        return len(self.datasource)

    def columnCount(self, parent=None):
        return 4

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = self.datasource[index.row()]
            if index.column() == COLUMN_ITEM_SKU:
                if 'item' in row and 'sku' in row['item']:
                    return row['item']['sku']
            elif index.column() == COLUMN_ITEM_DESCRIPTION:
                if 'item' in row and 'description' in row['item']:
                    return row['item']['description']
            elif index.column() == COLUMN_PERIOD:
                if 'period' in row:
                    return row['period']
            elif index.column() == COLUMN_DEMAND:
                if 'demand' in row:
                    return str(row['demand'])
        elif role == Qt.EditRole:
            data = self.datasource[index.row()]
            if index.column() == COLUMN_ITEM_SKU:
                if 'item' in data and 'sku' in data['item']:
                    return data['item']['sku']
            elif index.column() == COLUMN_ITEM_DESCRIPTION:
                if 'item' in data and 'description' in data['item']:
                    return data['item']['description']
            elif index.column() == COLUMN_PERIOD:
                if 'period' in data:
                    return data['period']
            elif index.column() == COLUMN_DEMAND:
                if 'demand' in data:
                    return data['demand']

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == COLUMN_ITEM_SKU:
                return 'item_sku'
            elif section == COLUMN_ITEM_DESCRIPTION:
                return 'item_description'
            elif section == COLUMN_PERIOD:
                return 'period'
            elif section == COLUMN_DEMAND:
                return 'demand'

    def item_updated(self, index):
        topleft = self.index(index, 0, QModelIndex())
        bottomright = self.index(index, self.columnCount() - 1 if self.columnCount() > 0 else 0)
        self.dataChanged.emit(topleft, bottomright)

    def insert_item(self, index=None, item=None):
        if index is None:
            index = len(self.datasource)
        if item is None:
            item = dict()
        self.beginInsertRows(QModelIndex(), index, index)
        self.datasource.insert(index, item)
        self.endInsertRows()

    def remove_item(self, index):
        self.beginRemoveRows(QModelIndex(), index, index)
        del self.datasource[index]
        self.endRemoveRows()

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        data = self.datasource[index.row()]
        if index.column() in [COLUMN_ITEM_SKU, COLUMN_ITEM_DESCRIPTION]:
            if 'item' not in data:
                flags |= Qt.ItemIsEditable
        else:
            flags |= Qt.ItemIsEditable

        return flags

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if index.column() == COLUMN_ITEM_SKU:
                if self.handler_changing_item_sku is not None:
                    self.handler_changing_item_sku(index.row(), value)
                    return True
            elif index.column() == COLUMN_ITEM_DESCRIPTION:
                if self.handler_changing_item_description is not None:
                    self.handler_changing_item_description(index.row(), value)
                    return True
            elif index.column() == COLUMN_DEMAND:
                if self.handler_changing_demand is not None:
                    self.handler_changing_demand(index.row(), value)
                    return True
            elif index.column() == COLUMN_PERIOD:
                if self.handler_changing_demand is not None:
                    self.handler_changing_period(index.row(), value)
                    return True
        return False


class Table_View_Items_Demand(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.SingleSelection)

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.modelReset.connect(self.resizeColumnsToContents)
        model.dataChanged.connect(self.changes_in_model)
        self.setItemDelegateForColumn(COLUMN_DEMAND, Delegate_Integer(self))

    def changes_in_model(self, uno=None, dos=None, tres=None):
        self.resizeColumnsToContents()


class Central_Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.storage = None
        lbl_storage = QLabel('storage', self)
        self.btn_change_storage = QPushButton('change storage', self)
        lbl_storage_id = QLabel('id: ', self)
        lbl_storage_name = QLabel('name: ', self)
        lbl_storage_address = QLabel('address: ', self)
        self.lbl_storage_id = QLabel(self)
        self.lbl_storage_name = QLabel(self)
        self.lbl_storage_address = QLabel(self)

        def set_fixed(ll):
            ll.setFixedWidth(ll.fontMetrics().width(ll.text()))
        set_fixed(lbl_storage_id)
        set_fixed(lbl_storage_name)
        set_fixed(lbl_storage_address)

        self.tablemodelitemsdemand = Table_Model_Items_Demand(self)
        self._itemsdemand = list()
        self.tablemodelitemsdemand.datasource = self.itemsdemand
        self.tableviewitemsdemand = Table_View_Items_Demand(self)
        self.tableviewitemsdemand.setModel(self.tablemodelitemsdemand)

        layoutstorage = QGridLayout()
        layoutstorage.addWidget(lbl_storage, 0, 0)
        layoutstorage.addWidget(self.btn_change_storage, 0, 1, Qt.AlignRight)
        layoutstorage.addWidget(lbl_storage_id, 1, 0)
        layoutstorage.addWidget(self.lbl_storage_id, 1, 1)
        layoutstorage.addWidget(lbl_storage_name, 2, 0)
        layoutstorage.addWidget(self.lbl_storage_name, 2, 1)
        layoutstorage.addWidget(lbl_storage_address, 3, 0)
        layoutstorage.addWidget(self.lbl_storage_address, 3, 1)
        mainlayout = QVBoxLayout(self)
        mainlayout.addItem(layoutstorage)
        mainlayout.addWidget(self.tableviewitemsdemand)
        self.setLayout(mainlayout)

        self.btn_change_storage.clicked.connect(self.handle_btn_change_storage_clicked)
        self.tablemodelitemsdemand.handler_changing_item_sku = self.handle_table_model_items_changing_item_sku
        self.tablemodelitemsdemand.handler_changing_item_description = \
            self.handle_table_model_items_changing_item_description
        self.tablemodelitemsdemand.handler_changing_period = self.handle_table_model_items_changing_period
        self.tablemodelitemsdemand.handler_changing_demand = self.handle_table_model_items_changing_demand
        self.agent_valentine = Client('isis.valentine.item_demand', 'valentine')
        self.agent_itzamara = Client('isis.valentine.item_demand', 'valentine')

    def handle_btn_change_storage_clicked(self):
        searcher = Search_Storage(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.storage = searcher.selected
            self.update_storage_ui()
            msg = {'type_message': 'request', 'request_type': 'get', 'get': 'valentine/get_item_demand',
                   'storage': self.storage}
            answer = self.agent_valentine(msg)
            self.itemsdemand = answer['result']

    def handle_table_model_items_changing_item_sku(self, index, value):
        itemdemand = self.itemsdemand[index]
        if value is not None and value:
            for _itemdemand in self.itemsdemand:
                if 'item' in _itemdemand and 'sku' in _itemdemand['item'] and _itemdemand['item']['sku'] == value:
                    break
            else:
                if not ('sku' in itemdemand and itemdemand['sku'] == value):
                    msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': value}}
                    answer = self.agent_itzamara(msg)
                    if 'result' in answer and answer['result'] is not None:
                        itemdemand['item'] = {'sku': answer['result']['sku'],
                                              'description': answer['result']['description']}
                        if 'type' in answer['result']:
                            itemdemand['item']['type'] = answer['result']['type']
                    elif 'item' in itemdemand:
                        del itemdemand['sku']
        else:
            if 'item' in itemdemand:
                del itemdemand['sku']
        self.ending_handle_table_model_items(index)

    def handle_table_model_items_changing_item_description(self, index, value):
        itemdemand = self.itemsdemand[index]
        if value is not None and value:
            searcher = Search_Item(self)
            result = searcher.search(value)
            if result is not None:
                for _itemdemand in self.itemsdemand:
                    if 'item' in _itemdemand and 'sku' in _itemdemand['item'] and \
                                    _itemdemand['item']['sku'] == result['sku']:
                        break
                else:
                    itemdemand['item'] = {'sku': result['sku'], 'description': result['description']}
                    if 'type' in result:
                        itemdemand['item']['type'] = result['type']
            elif 'item' in itemdemand:
                del itemdemand['item']
        elif 'item' in itemdemand:
            del itemdemand['item']

        self.ending_handle_table_model_items(index)

    def handle_table_model_items_changing_period(self, index, value):
        itemdemand = self.itemsdemand[index]
        if value is not None and value:
            itemdemand['period'] = value
        elif 'period' in itemdemand:
            del itemdemand['period']
        self.ending_handle_table_model_items(index)

    def handle_table_model_items_changing_demand(self, index, value):
        itemdemand = self.itemsdemand[index]
        if value is not None and value > 0:
            itemdemand['demand'] = value
        elif 'demand' in itemdemand:
            del itemdemand['demand']
        self.ending_handle_table_model_items(index)

    def ending_handle_table_model_items(self, index):
        itemdemand = self.itemsdemand[index]
        if 'item' in itemdemand and self.storage is not None:
            msg = {'type_message': 'action', 'action': 'valentine/update_item_demand', 'item_demand': itemdemand,
                   'storage': self.storage}
            self.agent_valentine(msg)
        self.tablemodelitemsdemand.item_updated(index)
        if not self.contains_empty_items() and self.storage is not None:
            self.insert_itemdemand()

    def contains_empty_items(self):
        for itemdemand in self.itemsdemand:
            if 'item' not in itemdemand:
                return True
        else:
            return False

    def insert_itemdemand(self):
        self.tablemodelitemsdemand.insert_item()

    @property
    def itemsdemand(self):
        return self._itemsdemand

    @itemsdemand.setter
    def itemsdemand(self, x):
        self._itemsdemand = x
        self.tablemodelitemsdemand.datasource = self._itemsdemand
        if not self.contains_empty_items() and self.storage is not None:
            self.insert_itemdemand()

    def update_storage_ui(self):
        if self.storage is not None:
            if 'id' in self.storage:
                self.lbl_storage_id.setText(self.storage['id'])
            else:
                self.lbl_storage_id.setText('')
            if 'name' in self.storage:
                self.lbl_storage_name.setText(self.storage['name'])
            else:
                self.lbl_storage_name.setText('')
            if 'address' in self.storage:
                self.lbl_storage_address.setText(self.storage['address'])
            else:
                self.lbl_storage_address.setText('')
            if not self.contains_empty_items():
                self.insert_itemdemand()
        else:
            self.lbl_storage_id.setText('')
            self.lbl_storage_name.setText('')
            self.lbl_storage_address.setText('')


class Item_Demand(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(600, 500)
        self.setWindowTitle('Item_Demand')
        self.cwidget = Central_Widget(self)
        self.setCentralWidget(self.cwidget)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    vv = Item_Demand()
    vv.show()
    sys.exit(app.exec_())
