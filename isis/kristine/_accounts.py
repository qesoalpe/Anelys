from PySide.QtGui import QApplication, QTreeView, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMenu, QMenuBar
from PySide.QtGui import QTableView
from PySide.QtCore import QModelIndex, QAbstractItemModel, Qt, QAbstractTableModel
from decimal import Decimal
from babel.numbers import format_decimal, format_currency
from pymongo import MongoClient
from datetime import datetime, date, timedelta
from isodate import datetime_isoformat
from dict import Dict

d8757_1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
d8757_1.admin.authenticate('alejandro', '47exI4')

#
# class Split:
#     def __init__(self, tx, account, data_model=None):
#         self._tx = tx
#         self._account = account
#         self._data = data_model
#
#     @property
#     def tx(self):
#         return self._tx
#
#     @property
#     def data_model(self):
#         return self._data
#
#     @data_model.setter
#     def data_model(self, x):
#         data_model = x
#         self._data = data_model
#
#     @property
#     def num(self):
#         if self.data_model is not None and 'num' in self.data_model:
#             return self.data_model['num']
#         elif self._tx is not None and self._tx.data_model is not None and 'num' in self._tx.data_model:
#             return self._tx.data_model['num']
#         else:
#             return None
#
#     @property
#     def value(self):
#         if self.data_model is not None and 'value' in self.data_model:
#             value = self.data_model['value']
#             if not isinstance(value, Decimal):
#                 value = round(Decimal(value), 2)
#             return value
#         elif self._tx is not None and self._tx.data_model is not None:
#             value = self._tx.data_model['value']
#             if not isinstance(value, Decimal):
#                 value = round(Decimal(value), 2)
#             return value
#         else:
#             return None
#
#     @property
#     def description(self):
#         if self.data_model is not None and 'description' in self.data_model:
#             return self.data_model['description']
#         elif self._tx is not None and self._tx.data_model is not None and 'description' in self._tx.data_model:
#             return self._tx.data_model['description']
#         else:
#             return None
#
#     @property
#     def datetime(self):
#         if self.data_model is not None and 'datetime' in self.data_model:
#             return self.data_model['datetime']
#         elif self.tx is not None and 'datetime' in self.tx:
#             return self.tx['datetime']
#         else:
#             return None
#
#     def __contains__(self, item):
#         if item == 'tx_id':
#             if self.tx is not None and 'id' in self.tx:
#                 return True
#             else:
#                 return False
#         elif item == 'datetime':
#             if self.datetime is not None:
#                 return True
#             else:
#                 return False
#         elif item == 'num':
#             if self.num is not None:
#                 return True
#             else:
#                 return False
#         elif item == 'description':
#             if self.num is not None:
#                 return True
#             else:
#                 return False
#         elif item == 'value':
#             if self.value is not None:
#                 return True
#             else:
#                 return False
#         else:
#             return False
#
#     def __getitem__(self, item):
#         if item == 'tx_id':
#             if self.tx is not None and 'id' in self.tx:
#                 return self.tx['id']
#             else:
#                 raise KeyError(item)
#         elif item == 'datetime':
#             if 'datetime' in self.data_model:
#                 return self.data_model['datetime']
#             elif 'datetime' in self.tx:
#                 return self.tx['datetime']
#             else:
#                 raise KeyError(item)
#         elif item == 'num':
#             if self.num is not None:
#                 return self.num
#             else:
#                 raise KeyError(item)
#         elif item == 'description':
#             description = self.description
#             if description is not None:
#                 return description
#             else:
#                 raise KeyError(item)
#         elif item == 'value':
#             value = self.value
#             if value is not None:
#                 return value
#             else:
#                 raise KeyError(item)
#         else:
#             raise KeyError(item)
#
#
# class Transaction:
#     def __init__(self, account, data_model):
#         self._account = account
#         self._data = data_model
#         self._splits = None
#
#     @property
#     def splits(self):
#         if self._splits is not None:
#             return self._splits
#         else:
#             if self.data_model is not
#             #d8757_1.kristine.transaction.find({'id': self.id}, {'_id': }
#
# class Account:
#     def __init__(self):
#         self._id = None
#         self._name = None
#         self._parent = None
#         self._children = None
#         self._txs = None
#         self._splits = None
#         self._data = None
#
#     @property
#     def id(self):
#         return self._id
#
#
# class repo_:
#     pass
#
#
# repo_account = list()
# repo_transaction = list()
# repo_split = list()
#
#
# class Account:
#     def __init__(self):
#         self._splits = None
#
#     @property
#     def splits(self):
#         if self._splits is not None:
#             return self._splits
#         else:
#             self._splits = get_splits_of_account(self)
#
#
# def find_account(filter=None):
#     if filter is not None:
#         if 'id' in filter:
#             for account in repo_account:
#                 if account['id'] == filter['id']:
#                     return account
#             else:
#                 account = d8757_1.kristine.account.find_one({'id': filter['id']}, {'_id': False})
#                 if account is not None:
#                     return account
#                 else:
#                     return None
#
#     result = list()
#     for account in repo_account:
#         result.append(account)
#     return result
#
#
# def ensure_account_singleton(account):
#     for _account in repo_account:
#         if _account['id'] == account['id']:
#             return _account
#     else:
#         if account['id'] == 'root':
#             repo_account.append(account)
#             return account
#         result = d8757_1.kristine.account.find_one({'id': account['id']}, {'_id': False})
#
#         if result is not None:
#             account = result
#             repo_account.append(account)
#             txs = list()
#             for tx in d8757_1.kristine.transaction.find({'splits.account.id': account['id']}):
#                 tx = ensure_tx_singleton(tx)
#                 txs.append(tx)
#             account['txs'] = txs
#             if 'parent' in account:
#                 account['parent'] = ensure_account_singleton(account)
#             return result
#         else:
#             return account
#
#
# def ensure_tx_singleton(tx):
#     for _tx in repo_transaction:
#         if _tx['id'] == tx['id']:
#             return _tx
#     else:
#         if 'splits' not in tx:
#             tx = d8757_1.kristine.transaction.find_one({'id': tx['id']}, {'_id': False})
#         for split in tx['splits']:
#             split['tx'] = tx
#             if 'account' in split:
#                 account = ensure_account_singleton(split['account'])
#                 if 'splits' not in account:
#                     account['splits'] = list()
#                 account['splits'].append(split)
#                 split['account'] = account
#         repo_transaction.append(tx)
#         return tx
#
#
class Model_Transactions(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None

    def rowCount(self, parent=None):
        if self.datasource is not None:
            return len(self.datasource)
        else:
            return 0

    def columnCount(self, parent=None):
        return 5

    @property
    def datasource(self):
        return self._datasource

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self.COLUMN_TX_ID:
                return 'tx_id'
            elif section == self.COLUMN_DATETIME:
                return 'datetime'
            elif section == self.COLUMN_NUM:
                return 'num'
            elif section == self.COLUMN_DESCRIPTION:
                return 'description'
            elif section == self.COLUMN_VALUE:
                return 'value'

    @datasource.setter
    def datasource(self, datasource):
        self._datasource = datasource
        self.modelReset.emit()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self.datasource[index.row()]
            if isinstance(data, dict):
                if index.column() == self.COLUMN_TX_ID:
                    if 'tx_id' in data:
                        return data['tx_id']
                elif index.column() == self.COLUMN_DATETIME:
                    if 'datetime' in data:
                        _datetime = data['datetime']
                        if isinstance(_datetime, str):
                            return _datetime
                        elif isinstance(_datetime, datetime):
                            return datetime_isoformat(_datetime)
                elif index.column() == self.COLUMN_NUM:
                    if 'num' in data:
                        num = data['num']
                        if isinstance(num, str):
                            return num
                        else:
                            return str(num)
                elif index.column() == self.COLUMN_DESCRIPTION:
                    if 'description' in data:
                        return data['description']
                elif index.column() == self.COLUMN_VALUE:
                    if 'value' in data:
                        value = data['value']
                        if isinstance(value, str):
                            return value
                        elif isinstance(value, (Decimal, float, int)):
                            return format_decimal(value, '#,##0.00', locale='es_mx')

    # def index(self, row, column, parent):
    #     data_model = self.datasource[row]
    #     return self.createIndex(row, column, data_model)

    COLUMN_TX_ID = 0
    COLUMN_DATETIME = 1
    COLUMN_NUM = 2
    COLUMN_DESCRIPTION = 3
    COLUMN_VALUE = 4


class Viewer_Transactions(QMainWindow):
    def __init__(self, parent):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('viewer transactions')
        self.resize(500, 500)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        layout_main = QVBoxLayout(self.cwidget)
        self.view = QTableView(self.cwidget)
        layout_main.addWidget(self.view)

        self._account = None
        self.model = Model_Transactions(self)
        self.view.setModel(self.model)


    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, account):
        self._account = account
        if 'splits' not in account:
            cursor = d8757_1.kristine.transaction.find({'splits.account.id': account['id']}, {'_id': False})
            splits = list()
            for tx in cursor:
                if 'splits' in tx:
                    for split in tx['splits']:
                        if 'account' in split and 'id' in split['account'] and split['account']['id'] == account['id']:
                            split['tx_id'] = tx['id']
                            if 'datetime' not in split and 'datetime' in tx:
                                split['datetime'] = tx['datetime']
                            if 'description' not in split and 'description' in tx:
                                split['description'] = tx['description']
                            if 'num' not in split and 'num' in tx:
                                split['num'] = tx['num']
                            splits.append(split)
            account['splits'] = splits
        else:
            splits = account['splits']
        self.model.datasource = splits


class TreeItem:
    def __init__(self, data=None):
        self.parent = None
        self.children = list()
        if data is not None and isinstance(data, dict):
            self._data = data
            if 'children' in data:
                for child_data in data['children']:
                    child_item = TreeItem(child_data)
                    child_item.parent = self
                    self.children.append(child_item)
        else:
            self._data = None

    def appendChild(self, child):
        self.children.append(child)

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return 4

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self._data is None:
                return None
            if column == self.COLUMN_NAME:
                if 'name' in self._data:
                    return self._data['name']
            elif column == self.COLUMN_ID:
                if 'id' in self._data:
                    return self._data['id']
            elif column == self.COLUMN_DESCRIPTION:
                if 'description' in self._data:
                    return self._data['description']
            elif column == self.COLUMN_BALANCE:
                if 'balance' in self._data:
                    if isinstance(self._data['balance'], Decimal):
                        return format_currency(self._data['balance'], 'MXN', '')

    def child(self, row):
        if len(self.children) <= 0:
            return None
        try:
            return self.children[row]
        except:
            print(self, row)

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)
        else:
            return None

    COLUMN_NAME = 1
    COLUMN_ID = 0
    COLUMN_DESCRIPTION = 2
    COLUMN_BALANCE = 3


class ModelTree(QAbstractItemModel):
    def __init__(self):
        QAbstractItemModel.__init__(self)
        self._datasource = None
        self._root_item = None

    def rowCount(self, parent=None):
        if not parent.isValid():
            parentItem = self.root_item
        else:
            parentItem = parent.internalPointer()
        if parentItem is not None:
            return parentItem.childCount()
        else:
            return 0

    def columnCount(self, parent=None):
        return 4

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        item = index.internalPointer()
        return item.data(index.column(), role)

    @property
    def root_item(self):
        return self._root_item

    @root_item.setter
    def root_item(self, x):
        if x is not None:
            self._root_item = TreeItem(x)
        else:
            self._root_item = None

    def index(self, row, column, parent):
        if not parent.isValid():
            parentItem = self.root_item
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.root_item:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.COLUMN_NAME:
                return 'name'
            elif section == self.COLUMN_ID:
                return 'id'
            elif section == self.COLUMN_DESCRIPTION:
                return 'description'
            elif section == self.COLUMN_BALANCE:
                return 'balance'


    COLUMN_NAME = 1
    COLUMN_ID = 0
    COLUMN_DESCRIPTION = 2
    COLUMN_BALANCE = 3


class TreeViewAccounts(QTreeView):
    def __init__(self, parent=None):
        QTreeView.__init__(self, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                account = index.internalPointer()._data
                menu = QMenu(self)
                action_view_txs = menu.addAction('view_txs')
                def view_txs():
                    viewer = Viewer_Transactions(self.parent())
                    viewer.account = account
                    viewer.show()
                action_view_txs.triggered.connect(view_txs)
                menu.popup(event.globalPos())



        QTreeView.mousePressEvent(self, event)

class Accounts(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(500, 500)
        self.setWindowTitle('kristine/accounts')
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)
        self.treeview = TreeViewAccounts(self.cwidget)
        layout_main = QVBoxLayout(self.cwidget)
        layout_main.addWidget(self.treeview)
        self.cwidget.setLayout(layout_main)

        self.model = ModelTree()
        self.treeview.setModel(self.model)
        self._accounts = None



        def _help(_account_parent):
            accounts = list()
            for account in d8757_1.kristine.account.find({'parent.id': _account_parent['id']}, {'_id': False}):
                accounts.append(account)
                account['parent'] = _account_parent
            if len(accounts) > 0:
                for account in accounts:
                    _help(account)
                _account_parent['children'] = accounts

        parent = {'id': 'root'}
        _help(parent)
        self.model.root_item = parent
        self.treeview.expandAll()
        for i in range(0, self.model.columnCount()):
            self.treeview.resizeColumnToContents(i)

    @property
    def accounts(self):
        return self._accounts

    @accounts.setter
    def accounts(self, x):
        self._accounts = x
        if x is not None:
            self.model.datasource = x

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    vv = Accounts()
    vv.show()
    sys.exit(app.exec_())
