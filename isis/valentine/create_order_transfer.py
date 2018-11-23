from decimal import Decimal
from PySide.QtCore import *
from PySide.QtGui import *
from babel.numbers import format_decimal
from babel.numbers import parse_decimal
from sarah.acp_bson import Client
from isis.itzamara.search_item import Search_Item
from isis.valentine.search_storage import Search_Storage

def set_width_fixed(ww):
    ww.setFixedWidth(ww.fontMetrics().width(ww.text()))

class Table_View_Items(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.dataChanged.connect(self.handler_changes)
        model.modelReset.connect(self.handler_changes)
        model.rowsInserted.connect(self.handler_changes)
        model.rowsRemoved.connect(self.handler_changes)

    def handler_changes(self, *args):
        self.resizeColumnsToContents()


class Model_Items(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None
        self.handler_changing_sku = None
        self.handler_changing_quanty = None
        self.handler_changing_description = None

    def columnCount(self, parent=None):
        return 5

    def rowCount(self, parent=None):
        if self._datasource is not None and isinstance(self._datasource, list):
            return len(self._datasource)
        else:
            return 0

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self.COLUMN_SKU:
                return 'sku'
            elif section == self.COLUMN_QUANTY:
                return 'quanty'
            elif section == self.COLUMN_DESCRIPTION:
                return 'description'
            elif section == self.COLUMN_MASS:
                return 'mass'
            elif section == self.COLUMN_MASS_NET:
                return 'mass_net'

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_SKU:
                if 'sku' in data:
                    return data['sku']
            elif index.column() == self.COLUMN_QUANTY:
                if 'quanty' in data:
                    return format_decimal(data['quanty'], '#,##0.###', locale='es_mx')
            elif index.column() == self.COLUMN_DESCRIPTION:
                if 'description' in data:
                    return data['description']
            elif index.column() == self.COLUMN_MASS:
                if 'mass' in data:
                    return format_decimal(data['mass']['n'], '#,##0.###', locale='es_mx') + data['mass']['unit']
            elif index.column() == self.COLUMN_MASS_NET:
                if 'quanty' in data and 'mass' in data:
                    return format_decimal(data['quanty'] * data['mass']['n'], '#,##0.###', locale='es_mx') \
                           + data['mass']['unit']
        elif role == Qt.EditRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_SKU:
                if 'sku' in data:
                    return data['sku']
            elif index.column() == self.COLUMN_DESCRIPTION:
                if 'description' in data:
                    return data['description']
            elif index.column() == self.COLUMN_QUANTY:
                if 'quanty' in data:
                    return format_decimal(data['quanty'], '#,##0.###', locale='es_mx')

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if index.column() == self.COLUMN_SKU:
                if self.handler_changing_sku is not None:
                    self.handler_changing_sku(index.row(), value)
                    return True
            elif index.column() == self.COLUMN_QUANTY:
                if self.handler_changing_quanty is not None:
                    self.handler_changing_quanty(index.row(), parse_decimal(value, locale='es_mx'))
                    return True

            elif index.column() == self.COLUMN_DESCRIPTION:
                if self.handler_changing_description is not None:
                    self.handler_changing_description(index.row(), value)
                    return True
        return False

    def contains_empty_items(self):
        for data in self.datasource:
            if 'description' not in data:
                return True
        else:
            return False

    def item_updated(self, index):
        topleft = self.index(index, 0, QModelIndex())
        bottomright = self.index(index, self.columnCount() - 1 if self.columnCount() > 0 else 0)
        self.dataChanged.emit(topleft, bottomright)

    def insert_item(self, index=None, item=None):
        if item is None:
            item = dict()
        if index is None:
            index = 0
            for _item in self._datasource:
                if 'description' not in _item:
                    break
                else:
                    index += 1

        self.beginInsertRows(QModelIndex(), index, index)
        self._datasource.insert(index, item)
        self.endInsertRows()


    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() not in [self.COLUMN_MASS, self.COLUMN_MASS_NET]:
            flags |= Qt.ItemIsEditable
        return flags

    COLUMN_SKU = 0
    COLUMN_QUANTY = 1
    COLUMN_DESCRIPTION = 2
    COLUMN_MASS = 3
    COLUMN_MASS_NET = 4


class Create_Order_Transfer(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Create_Order_Transfer')
        self.resize(500, 500)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        lbl_from = QLabel('from', self.cwidget)
        lbl_from_id = QLabel('id: ', self.cwidget)
        lbl_from_name = QLabel('name: ', self.cwidget)

        lbl_to = QLabel('to', self.cwidget)
        lbl_to_id = QLabel('id: ', self.cwidget)
        lbl_to_name = QLabel('name: ', self.cwidget)

        btn_change_from = QPushButton('change_from', self.cwidget)
        self.lbl_from_id = QLabel(self.cwidget)
        self.lbl_from_name = QLabel(self.cwidget)

        btn_change_to = QPushButton('change_to', self.cwidget)
        self.lbl_to_id = QLabel(self.cwidget)
        self.lbl_to_name = QLabel(self.cwidget)

        set_width_fixed(lbl_from)
        set_width_fixed(lbl_from_id)
        set_width_fixed(lbl_from_name)
        set_width_fixed(lbl_to)
        set_width_fixed(lbl_to_id)
        set_width_fixed(lbl_to_name)

        self.tableviewitems = Table_View_Items(self.cwidget)
        layoutstorages = QGridLayout()
        layoutstorages.addWidget(lbl_from, 0, 0)
        layoutstorages.addWidget(btn_change_from, 0, 1, Qt.AlignRight)
        layoutstorages.addWidget(lbl_from_id, 1, 0)
        layoutstorages.addWidget(self.lbl_from_id, 1, 1)
        layoutstorages.addWidget(lbl_from_name, 2, 0)
        layoutstorages.addWidget(self.lbl_from_name, 2, 1)
        layoutstorages.addWidget(lbl_to, 0, 2)
        layoutstorages.addWidget(btn_change_to, 0, 3, Qt.AlignRight)
        layoutstorages.addWidget(lbl_to_id, 1, 2)
        layoutstorages.addWidget(self.lbl_to_id, 1, 3)
        layoutstorages.addWidget(lbl_to_name, 2, 2)
        layoutstorages.addWidget(self.lbl_to_name, 2, 3)

        layoutmain = QVBoxLayout(self.cwidget)
        layoutmain.addItem(layoutstorages)
        layoutmain.addWidget(self.tableviewitems)
        self.cwidget.setLayout(layoutmain)

        self.modelitems = Model_Items(self.cwidget)
        self._items = list()
        self.modelitems.datasource = self._items
        if not self.modelitems.contains_empty_items():
            self.modelitems.insert_item()
        self.tableviewitems.setModel(self.modelitems)

        self.modelitems.handler_changing_sku = self.handle_modelitems_changing_sku
        self.modelitems.handler_changing_quanty = self.handle_modelitems_changing_quanty
        self.modelitems.handler_changing_description = self.handle_modelitems_changing_description
        btn_change_from.clicked.connect(self.handle_btn_change_from_clicked)
        btn_change_to.clicked.connect(self.handle_btn_change_to_clicked)

        self.agent_itzamara = Client('Create_Order_Transfer', 'itzamara')

    def handle_btn_change_from_clicked(self):
        pass

    def handle_btn_change_to_clicked(self):
        pass

    def handle_modelitems_changing_sku(self, index, value):
        item = self.items[index]
        if value is not None and value:
            if 'sku' in item and item['sku'] == value:
                return
            answer = self.agent_itzamara(msg = {'type_message': 'find_one', 'type': 'itzamara/item',
                                                'query': {'sku': value}})
            if 'result' in answer and answer['result'] is not None:
                self.set_item_in_old(item, answer['result'])
            else:
                for k in list(item.keys()):
                    if k in ['sku', 'type', 'description', 'mass']:
                        del item[k]
        else:
            for k in list(item.keys()):
                if k in ['sku', 'type', 'description', 'mass']:
                    del item[k]
        self.ending_handle_modelitems_changing(index)

    def set_item_in_old(self, old, new):
        result = new
        item = old
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

        if 'mass' in result:
            item['mass'] = result['mass']
        else:
            answer = self.agent_itzamara({'type_message': 'request', 'request_type': 'get',
                                          'get': 'itzamara/get_item_mass', 'item': item})
            if 'mass' in answer and answer['mass'] is not None:
                item['mass'] = answer['mass']
            elif 'mass' in item:
                del item['mass']

    def handle_modelitems_changing_quanty(self, index, value):
        item = self.items[index]
        if value is not None and value > Decimal(0):
            item['quanty'] = value
        elif 'quanty' in item:
            del item['quanty']
        self.ending_handle_modelitems_changing(index)

    def handle_modelitems_changing_description(self, index, value):
        item = self.items[index]
        if value is not None and value:
            if 'description' in item and item['description'] == value:
                return
            searcher = Search_Item(self.cwidget)
            result = searcher.search(value)
            if result is not None:
                self.set_item_in_old(item, result)
            else:
                for k in list(item.keys()):
                    if k in ['sku', 'type', 'description', 'mass']:
                        del item[k]
        else:
            for k in list(item.keys()):
                if k in ['sku', 'type', 'description', 'mass']:
                    del item[k]
        self.ending_handle_modelitems_changing(index)

    def ending_handle_modelitems_changing(self, index):
        self.modelitems.item_updated(index)
        if not self.modelitems.contains_empty_items():
            self.modelitems.insert_item()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, x):
        self._items = x
        self.modelitems.datasource = self._items


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Create_Order_Transfer()
    vv.show()
    sys.exit(app.exec_())
