import copy
from PySide.QtCore import *
from PySide.QtGui import *
import sys
from decimal import Decimal
from pymongo import MongoClient
from sarah.acp_bson import Client, dictutils
import json
from babel.numbers import format_currency
from isis.item_delegate import Money_Delegate, Decimal_Delegate
agent_perla = Client('isis.benefit_of_new_purchase_prices', 'perla')
mongo_local = MongoClient(host='mongodb://127.0.0.1', port=27020)
APP_ID = '31-12'
db_app = mongo_local.get_database(APP_ID)


COLUMN_PP_ID = 0
COLUMN_PP_VALUE = 1
COLUMN_PRODUCT_SKU = 2
COLUMN_PRODUCT_DESCRIPTION = 3
COLUMN_CONDITIONS = 4
COLUMN_P_ID = 5
COLUMN_P_DESCRIPTION = 6
COLUMN_P_VALUE = 7
COLUMN_BENEFIT = 8


def calc_benefit(cost, price):
    return round(((price / cost) -1 )*100, 2)


class Data_Table_Model_Items(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.rows = list()
        self.changing_p_value = None
        self.changing_benefit = None
        self.resizecolumns = None

    def set_rows(self, rows):
        i = len(self.rows) - 1
        self.beginRemoveRows(QModelIndex(), 0, i)
        self.rows.clear()
        self.endRemoveRows()
        self.rows = rows
        i = len(self.rows) - 1
        self.beginInsertRows(QModelIndex(), 0, i)
        self.endInsertRows()

    def rowCount(self, parent):
        return len(self.rows)

    def columnCount(self, parent):
        return 9

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == COLUMN_PP_ID:
                return 'pp_id'
            elif section == COLUMN_PP_VALUE:
                return 'pp_value'
            elif section == COLUMN_PRODUCT_SKU:
                return 'product_sku'
            elif section == COLUMN_PRODUCT_DESCRIPTION:
                return 'product_description'
            elif section == COLUMN_CONDITIONS:
                return 'conditions'
            elif section == COLUMN_P_ID:
                return 'p_id'
            elif section == COLUMN_P_DESCRIPTION:
                return 'p_description'
            elif section == COLUMN_P_VALUE:
                return 'p_value'
            elif section == COLUMN_BENEFIT:
                return 'benefit'

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = self.rows[index.row()]
            column = index.column()
            if column == COLUMN_PP_ID:
                if 'pp_id' in row:
                    return row['pp_id']
            elif column == COLUMN_PP_VALUE:
                if 'pp_value' in row:
                    return format_currency(row['pp_value'], currency='MXN', locale='es_mx')
            elif column == COLUMN_PRODUCT_SKU:
                if 'product_sku' in row:
                    return row['product_sku']
            elif column == COLUMN_PRODUCT_DESCRIPTION:
                if 'product_description' in row:
                    return row['product_description']
            elif column == COLUMN_CONDITIONS:
                if 'conditions' in row:
                    return row['conditions']
            elif column == COLUMN_P_ID:
                if 'p_id' in row:
                    return row['p_id']
            elif column == COLUMN_P_DESCRIPTION:
                if 'p_description' in row:
                    return row['p_description']
            elif column == COLUMN_P_VALUE:
                if 'p_value' in row:
                    return format_currency(row['p_value'], currency='MXN', locale='es_MX')
            elif column == COLUMN_BENEFIT:
                if 'benefit' in row:
                    return str(row['benefit'])
        elif role == Qt.EditRole:
            row = self.rows[index.row()]
            column = index.column()
            if column == COLUMN_P_VALUE:
                if 'p_value' in row:
                    return row['p_value']
            elif column == COLUMN_BENEFIT:
                if 'benefit' in row:
                    return row['benefit']

    def setData(self, index, value, role):
        if role == Qt.EditRole and index.isValid():
            column = index.column()
            row = self.rows[index.row()]
            if column == COLUMN_P_VALUE:
                if self.changing_p_value is not None:
                    self.changing_p_value(row, value)
                    return True
            elif column == COLUMN_BENEFIT:
                if self.changing_benefit is not None:
                    self.changing_benefit(row, value)
                    return True
        return False

    def insert_row(self, i, row):
        self.rows.insert(i, row)
        self.beginInsertRows(QModelIndex(), i, i)
        self.endInsertRows()

    def remove_row(self, index=None, row=None):
        if index is not None:
            del self.rows[index]
            self.beginRemoveRows(QModelIndex(), index, index)
            self.endRemoveRows()
        elif row is not None:
            i = 0
            for rr in self.rows:
                if row is rr:
                    break
                i += 1
            else:
                i -1
            if i >= 0:
                del self.rows[i]
                self.beginRemoveRows(QModelIndex(), i, i)
                self.endRemoveRows()

    def update_row(self, index=None, row=None):
        if index is not None:
            topleft, bottonright = self._get_indexes(index)
            self.dataChanged.emit(topleft, bottonright)
        elif row is not None:
            i = self.rows.index(row)
            topleft, bottonright = self._get_indexes(i)
            self.dataChanged.emit(topleft, bottonright)

    def insert_row(self, i, r):
        self.beginInsertRows(QModelIndex(), i, i)
        self.rows.insert(i, r)
        self.endInsertRows()

    def _get_indexes(self, i):
        topleft = self.index(i, 0)
        bottomright = self.index(i, 8)
        return topleft, bottomright

    def add_row(self, row):
        self.rows.append(row)
        i = self.rows.index(row)
        self.beginInsertRows(QModelIndex(), i, i)
        self.endInsertRows()

    def update_item(self, item, resizecolumns=True):
        one = None
        two = None
        i = 0
        for row in self.rows[:]:
            if 'product_sku' in row and item['product']['sku'] == row['product_sku']:
                one = row
                break
            i += 1
        if one is not None and i != len(self.rows) - 1:
            for row in self.rows[i+1:]:
                if 'product_sku' in row and item['product']['sku'] == row['product_sku']:
                    two = row
                    break
        if 'price' in item:
            if one is None:
                one = dict()
                one['pp_id'] = item['purchase_price']['id']
                one['pp_value'] = item['purchase_price']['value']
                one['product_sku'] = item['product']['sku']
                one['product_description'] = item['product']['description']
                self.add_row(one)
            price = item['price']
            one['p_id'] = price['id']
            if 'description' in price:
                one['p_description'] = price['description']
            elif 'p_description' in one:
                del one['p_description']
            one['p_value'] = price['value']
            one['benefit'] = calc_benefit(cost=item['purchase_price']['value'], price=price['value'])
            self.update_row(row=one)
            if two is not None:
                self.remove_row(row=two)
        elif 'prices' in item:
            if one is None:
                one = dict()
                one['pp_id'] = item['purchase_price']['id']
                one['pp_value'] = item['purchase_price']['value']
                one['product_sku'] = item['product']['sku']
                one['product_description'] = item['product']['description']
                self.add_row(row=one)
            price = item['prices'][0]
            one['p_id'] = price['id']
            one['p_value'] = price['value']
            one['p_description'] = price['description']
            one['benefit'] = calc_benefit(cost=item['purchase_price']['value'], price=price['value'])
            self.update_row(row=one)
            if two is None:
                i = self.rows.index(one) + 1
                two = dict()
                two['pp_id'] = item['purchase_price']['id']
                two['pp_value'] = item['purchase_price']['value']
                two['product_sku'] = item['product']['sku']
                two['product_description'] = item['product']['description']
                self.insert_row(i, two)
            price = item['prices'][1]
            two['p_id'] = price['id']
            two['p_value'] = price['value']
            two['p_description'] = price['description']
            two['benefit'] = calc_benefit(cost=item['purchase_price']['value'], price=price['value'])
            self.update_row(row=two)
        else:
            if one is not None:
                if 'p_id' in one:
                    del one['p_id']
                if 'p_value' in one:
                    del one['p_value']
                if 'p_description' in one:
                    del one['p_description']
                if 'benefit' in one:
                    del one['benefit']
                self.update_row(row=one)
            else:
                one = dict()
                one['pp_id'] = item['purchase_price']['id']
                one['pp_value'] = item['purchase_price']['value']
                one['product_sku'] = item['product']['sku']
                one['product_description'] = item['product']['description']
                self.add_row(one)
            if two is not None:
                self.remove_row(row=two)
        if resizecolumns and self.resizecolumns is not None:
            self.resizecolumns()

    def flags(self, index):
        flag = Qt.ItemIsEnabled

        if index.column() in [COLUMN_P_VALUE, COLUMN_BENEFIT]:
            flag |= Qt.ItemIsEditable
        return flag

    def clear(self):
        self.beginRemoveRows(QModelIndex(), 0, len(self.rows) - 1)
        self.rows.clear()
        self.endRemoveRows()


class Table_View(QTableView):
    def __init__(self, parent):
        QTableView.__init__(self, parent)

    def setModel(self, model):
        QTableView.setModel(self, model)
        self.setItemDelegateForColumn(COLUMN_P_VALUE, Money_Delegate(self))
        self.setItemDelegateForColumn(COLUMN_BENEFIT, Decimal_Delegate(self))
        if hasattr(model, 'resizecolumns'):
            model.resizecolumns = self.resizeColumnsToContents


class Central_Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.items = list()
        self.prices = list()
        self.products = list()
        self.actions_price_change_value = list()
        self.tablemodel = Data_Table_Model_Items()
        self.tableview = Table_View(self)
        self.tableview.setModel(self.tablemodel)
        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.tableview, 0, 0)
        self.setLayout(self.main_layout)
        self.doc = {'items': self.items, 'prices': self.prices, 'products': self.products, 'actions_price_change_value':
            self.actions_price_change_value, 'tablemodel': self.tablemodel.rows}
        self.tablemodel.changing_benefit = self.handler_changing_benefit
        self.tablemodel.changing_p_value = self.handler_changing_p_value

    def get_doc_encoded_str_json(self):
        dictutils.dec_to_float(self.doc)
        str_json = json.dumps(self.doc, ensure_ascii=False, indent=2)
        dictutils.float_to_dec(self.doc)
        return str_json

    def set_doc(self, doc):
        self.items = doc['items']
        self.prices = doc['prices']
        self.products = doc['products']
        self.actions_price_change_value = doc['actions_price_change_value']
        self.tablemodel.set_rows(doc['tablemodel'])
        self.tableview.resizeColumnsToContents()

    def set_doc_with_items(self, items):
        self.items = items
        self.prices = list()
        self.products = list()
        self.actions_price_change_value = list()

        self.tablemodel.clear()
        for item in self.items:
            self.tablemodel.update_item(item)
            self.add_product_unique(item['product'])
            if 'price' in item:
                self.add_price_unique(item['price'])
            elif 'prices' in item:
                for price in item['prices']:
                    self.add_price_unique(price)
        self.doc = {'items': self.items, 'prices': self.prices, 'products': self.products, 'actions_price_change_value':
            self.actions_price_change_value, 'tablemodel': self.tablemodel.rows}
        self.tableview.resizeColumnsToContents()

    def add_product_unique(self, product):
        for pp in self.products:
            if pp['sku'] == product['sku']:
                return
        else:
            self.products.append(product)

    def add_price_unique(self, price):
        for pp in self.prices:
            if pp['id'] == price['id']:
                return
        else:
            price = copy.deepcopy(price)
            for k in list(price.keys()):
                if k not in ['id', 'type', 'description', 'value']:
                    del price[k]
            self.prices.append(price)

    def action_save_as_file_app(self):
        filename = QFileDialog.getSaveFileName(self, 'choose a file', 'C:\\', 'app\'s file(*.31-12.json)')
        if filename[0]:
            f = open(filename[0], 'wt', encoding='utf8')
            f.write(self.get_file_coded_in_json())
            f.close()

    def get_file_coded_in_json(self):
        return ''

    def update_price(self, price_id, value):
        price = self.search_price(price_id)
        price['value'] = value
        items = self.itemstable
        for row in items.rows:
            if 'price_id' in row and price_id == row['price_id']:
                row['price_id'] = value
                row['benefit'] = calc_benefit(cost=row['pp_value'], price=row['p_value'])

    def handler_changing_p_value(self, row, value):
        self.update_price(row['p_id'], value)

    def handler_changing_benefit(self, row, value):
        if value < 0:
            pass
        new_price = row['pp_value'] * (Decimal(1) + value)
        self.update_price(row['p_id'], new_price)

    def open_from_localhost_filesystem(self):
        filename = QFileDialog.getOpenFileName(self, 'open from localhost filesystem', '', '31-12\'s files(*.31-12.json)')
        filename = filename[0]
        if filename:
            f = open(filename, 'rt', encoding='utf8')
            doc = json.loads(f.read())
            self.set_doc(doc)

    def save_in_localhost_filesystem(self):
        filename = QFileDialog.getSaveFileName(self, 'save in localhost filesystem', '', '31-12\' file (*.31-12.json)')
        filename = filename[0]
        if filename:
            f = open(filename, 'wt', encoding='utf8')
            f.write(self.get_doc_encoded_str_json())
            f.close()

    def load_perla_items(self):
        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'perla/get_benefit_of_new_purchase_prices'}
        answer = agent_perla.send_msg(msg)
        self.set_doc_with_items(answer['items'])


class Main_Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('benefit_of_new_purchase_prices')
        self.resize(1300, 700)
        self.setCentralWidget(Central_Widget(self))
        self.create_toolbars()

    def create_toolbars(self):
        cw = self.centralWidget()
        assert isinstance(cw, Central_Widget)
        file_toolbar = self.addToolBar('file')
        action_open_from_host = QAction('Open from localhost filesystem', file_toolbar)
        file_toolbar.addAction(action_open_from_host)
        action_save_in_host = QAction('Save in localhost filesystem', file_toolbar)
        file_toolbar.addAction(action_save_in_host)
        action_load_perla_items = QAction('Load perla\'s items', file_toolbar)
        file_toolbar.addAction(action_load_perla_items)
        action_open_from_host.triggered.connect(cw.open_from_localhost_filesystem)
        action_save_in_host.triggered.connect(cw.save_in_localhost_filesystem)
        action_load_perla_items.triggered.connect(cw.load_perla_items)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mm = Main_Window()
    mm.show()
    sys.exit(app.exec_())
