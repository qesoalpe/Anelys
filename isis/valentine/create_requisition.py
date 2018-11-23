from PySide.QtCore import *
from PySide.QtGui import *
from babel.numbers import format_decimal, parse_decimal
from isis.itzamara.search_item import Search_Item
from isis.valentine.search_storage import Search_Storage
from sarah.acp_bson import Client


class Table_Model_Items(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None
        self.handler_changing_sku = None
        self.handler_changing_description = None
        self.handler_changed_quanty = None

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def rowCount(self, parent=None):
        if self._datasource is not None:
            return len(self._datasource)
        else:
            return 0

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_SKU:
                if 'sku' in data:
                    return data['sku']
            elif index.column() == self.COLUMN_QUANTY:
                if 'quanty' in data:
                    return format_decimal(data['quanty'], '#,###.###', 'es_mx')
            elif index.column() == self.COLUMN_DESCRIPTION:
                if 'description' in data:
                    return data['description']
        elif role == Qt.EditRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_SKU:
                if 'sku' in data:
                    return data['sku']
            elif index.column() == self.COLUMN_QUANTY:
                if 'quanty' in data:
                    return data['quanty']
            elif index.column() == self.COLUMN_DESCRIPTION:
                if 'description' in data:
                    return data['description']

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if index.column() == self.COLUMN_SKU:
                if self.handler_changing_sku is not None:
                    self.handler_changing_sku(index.row(), value)
                    return True
            elif index.column() == self.COLUMN_QUANTY:
                data = self._datasource[index.row()]
                value = parse_decimal(value, 'es_mx')
                data['quanty'] = value
                if self.handler_changed_quanty is not None:
                    self.handler_changed_quanty(index.row(), value)
                return True
            elif index.column() == self.COLUMN_DESCRIPTION:
                if self.handler_changing_description is not None:
                    self.handler_changing_description(index.row(), value)
                    return True
        return False

    def item_updated(self, index):
        topleft = self.index(index, 0, QModelIndex())
        bottomright = self.index(index, self.columnCount() - 1 if self.columnCount() > 0 else 0)
        self.dataChanged.emit(topleft, bottomright)

    def contains_empty_items(self):
        for item in self._datasource:
            if 'quanty' not in item or 'description' not in item:
                return True
        else:
            return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self.COLUMN_SKU:
                return 'sku'
            elif section == self.COLUMN_QUANTY:
                return 'quanty'
            elif section == self.COLUMN_DESCRIPTION:
                return 'description'

    def insert_item(self, index=None, item=None):
        if index is None:
            index = len(self._datasource)
        if item is None:
            item = dict()
        self.beginInsertRows(QModelIndex(), index, index)
        self._datasource.insert(index, item)
        self.endInsertRows()

    def remove_item(self, index):
        self.beginRemoveRows(QModelIndex(), index, index)
        del self._datasource[index]
        self.endRemoveRows()

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    COLUMN_SKU = 0
    COLUMN_QUANTY = 1
    COLUMN_DESCRIPTION = 2


class Table_View_Items(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.dataChanged.connect(self._handle_model_upate)
        model.modelReset.connect(self._handle_model_upate)

    def _handle_model_upate(self, uno=None, dos=None, tres=None):
        self.resizeColumnsToContents()


class Create_Requisition(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(600, 600)
        self.setWindowTitle('Create_Requisition')
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)
        self.tablemodelitems = Table_Model_Items(self.cwidget)
        lbl_storage = QLabel('storage', self.cwidget)
        btn_change_storage = QPushButton('change_storage', self.cwidget)
        lbl_storage_id = QLabel('id: ', self.cwidget)
        lbl_storage_type = QLabel('type: ', self.cwidget)
        lbl_storage_name = QLabel('name: ', self.cwidget)
        lbl_storage_address = QLabel('address: ', self.cwidget)
        self.lbl_storage_id = QLabel(self.cwidget)
        self.lbl_storage_type = QLabel(self.cwidget)
        self.lbl_storage_name = QLabel(self.cwidget)
        self.lbl_storage_address = QLabel(self.cwidget)
        lbl_to = QLabel('to', self.cwidget)
        btn_change_to = QPushButton('change_to', self.cwidget)
        btn_remove_to = QPushButton('remove_to', self.cwidget)
        lbl_to_id = QLabel('id: ', self.cwidget)
        lbl_to_type = QLabel('type: ', self.cwidget)
        lbl_to_name = QLabel('name: ', self.cwidget)
        lbl_to_address = QLabel('address: ', self.cwidget)
        self.lbl_to_id = QLabel(self.cwidget)
        self.lbl_to_type = QLabel(self.cwidget)
        self.lbl_to_name = QLabel(self.cwidget)
        self.lbl_to_address = QLabel(self.cwidget)
        storagelayout = QGridLayout()
        storagelayout.addWidget(lbl_storage, 0, 0)
        storagelayout.addWidget(btn_change_storage, 0, 1, Qt.AlignRight)
        storagelayout.addWidget(lbl_storage_id, 1, 0)
        storagelayout.addWidget(self.lbl_storage_id, 1, 1)
        storagelayout.addWidget(lbl_storage_type, 2, 0)
        storagelayout.addWidget(self.lbl_storage_type, 2, 1)
        storagelayout.addWidget(lbl_storage_name, 3, 0)
        storagelayout.addWidget(self.lbl_storage_name, 3, 1)
        storagelayout.addWidget(lbl_storage_address, 4, 0)
        storagelayout.addWidget(self.lbl_storage_address, 4, 1)
        tolayout = QGridLayout()
        tolayout.addWidget(lbl_to, 0, 0)
        # buttonslayout = QHBoxLayout()
        # buttonslayout.addStretch()
        # buttonslayout.addWidget(btn_remove_to)
        # buttonslayout.addWidget(btn_change_to)
        # tolayout.addItem(buttonslayout, 0, 1, Qt.AlignRight)
        tolayout.addWidget(btn_remove_to, 0, 1, Qt.AlignRight)
        tolayout.addWidget(btn_change_to, 0, 2, Qt.AlignRight)
        tolayout.addWidget(lbl_to_id, 1, 0)
        tolayout.addWidget(self.lbl_to_id, 1, 1, 1, -1)
        tolayout.addWidget(lbl_to_type, 2, 0)
        tolayout.addWidget(self.lbl_to_type, 2, 1, 1, -1)
        tolayout.addWidget(lbl_to_name, 3, 0)
        tolayout.addWidget(self.lbl_to_name, 3, 1, 1, -1)
        tolayout.addWidget(lbl_to_address, 4, 0)
        tolayout.addWidget(self.lbl_to_address, 4, 1, 1, -1)

        self.tableviewitems = Table_View_Items(self.cwidget)
        self.tableviewitems.setModel(self.tablemodelitems)
        self.items = list()
        self._storage = None
        self.tablemodelitems.datasource = self.items

        mainlayout = QVBoxLayout(self.cwidget)
        toplayout = QHBoxLayout()
        toplayout.addItem(storagelayout)
        toplayout.addItem(tolayout)
        mainlayout.addItem(toplayout)
        mainlayout.addWidget(self.tableviewitems)
        self.cwidget.setLayout(mainlayout)
        self.agent_itzamara = Client('isis.valentine.create_requisition', 'itzamara')
        self.tablemodelitems.handler_changing_sku = self.handle_table_model_changing_sku
        self.tablemodelitems.handler_changing_description = self.handle_table_model_changing_description
        self.tablemodelitems.handler_changed_quanty = self.handle_table_model_changed_quanty
        btn_change_storage.clicked.connect(self.handle_btn_change_storage_clicked)
        # btn_remove_to.clicked.connect(self.handle_btn_remove_to_clicked)
        btn_change_to.clicked.connect(self.handle_btn_change_to_clicked)
        if not self.contains_items_empty():
            self.tablemodelitems.insert_item()

    def handle_table_model_changed_quanty(self, index, value):
        if not self.contains_items_empty():
            self.tablemodelitems.insert_item()

    def handle_table_model_changing_sku(self, index, value):
        item = self.items[index]
        if value is not None and value:
            msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': value}}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer['result'] is not None:
                result = answer['result']
                if 'sku' in result:
                    item['sku'] = result
                elif 'sku' in item:
                    del item['sku']

                if 'description' in result:
                    item['description'] = result['description']
                elif 'description' in item:
                    del item['description']

                if 'type' in result:
                    item['type'] = result['type']
                elif 'type' in item:
                    del item['type']
            else:
                for key in list(item.keys()):
                    if key in ['sku', 'type', 'description']:
                        del item[key]
        else:
            for key in list(item.keys()):
                if key in ['sku', 'type', 'description']:
                    del item[key]
        self.tablemodelitems.item_updated(index)
        if not self.tablemodelitems.contains_empty_items():
            self.tablemodelitems.insert_item()

    def handle_table_model_changing_description(self, index, value):
        item = self.items[index]
        if value is not None and value:
            searcher = Search_Item(self)
            result = searcher.search(value)
            if result is not None:
                if 'type' in result:
                    item['type'] = result['type']
                elif 'type' in item:
                    del item['type']

                if 'sku' in result:
                    item['sku'] = result['sku']
                elif 'sku' in item:
                    del item['sku']

                if 'description' in result:
                    item['description'] = result['description']
                elif 'description' in item:
                    del item['description']

            else:
                if 'sku' in item:
                    del item['sku']
                if 'description' in item:
                    del item['description']
                if 'type' in item:
                    del item['type']
        else:
            if 'sku' in item:
                del item['sku']
            if 'description' in item:
                del item['description']
            if 'type' in item:
                del item['type']
        self.tablemodelitems.item_updated(index)
        if not self.contains_items_empty():
            self.tablemodelitems.insert_item()

    def handle_btn_change_storage_clicked(self):
        searcher = Search_Storage(self)
        searcher.exec_()
        if searcher.selected is not None:
            result = searcher.selected
            for k in list(result.keys()):
                if k not in ['id', 'name', 'type', 'address']:
                    del result[k]

            self._storage = result
            self.update_storage_ui()

    def handle_btn_change_to_clicked(self):
        if searcher.selected is not None:
            result = searcher.selected
            if result['type'] == 'valentine/storage':
                for k in list(result.keys()):
                    if k not in ['id', 'name', 'type', 'address']:
                        del result[k]
            else:  # if result['type'] == 'piper/provider':
                for k in list(result.keys()):
                    if k not in ['id', 'name', 'type']:
                        del result[k]
            self._storage = result

    def update_storage_ui(self):
        storage = self._storage
        if storage is not None:
            if 'id' in storage:
                self.lbl_storage_id.setText(storage['id'])
            else:
                self.lbl_storage_id.setText('')
            if 'type' in storage:
                self.lbl_storage_type.setText(storage['type'])
            else:
                self.lbl_storage_type.setText('')
            if 'name' in storage:
                self.lbl_storage_name.setText(storage['name'])
            else:
                self.lbl_storage_name.setText('')
            if 'address' in storage:
                self.lbl_storage_address.setText(storage['address'])
            else:
                self.lbl_storage_address.setText('')
        else:
            self.lbl_storage_id.setText('')
            self.lbl_storage_type.setText('')
            self.lbl_storage_name.setText('')
            self.lbl_storage_address.setText('')

    def contains_items_empty(self):
        return self.tablemodelitems.contains_empty_items()

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Create_Requisition()
    vv.show()
    sys.exit(app.exec_())
