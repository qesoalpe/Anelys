from isis.table_view import Table_View
from isis.data_model.table import Table
from isis.dialog import Dialog
from decimal import Decimal
from pymongo import MongoClient
from dict import Dict
from PySide.QtGui import QVBoxLayout, QMenu
from PySide.QtCore import Qt


d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
d1.admin.authenticate('alejandro', '47exI4')


class Splits_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('datetime', str)
        self.columns.add('num', int)
        self.columns.add('description', str)
        # self.columns.add('transfered', str)
        self.columns.add('debit', Decimal, 'c')
        self.columns.add('credit', Decimal, 'c')
        self.columns.add('balance', Decimal, 'c')
        self._account = None
        self.with_new_empty_row = False
        self.readonly = True

        def get_data_transfered(row):
            if 'tx' in row:
                tx = row.tx
                if 'splits' in tx and len(tx.splits) == 2 and 'id' in row:
                    splits = tx.splits
                    if 'id' not in splits[0] or splits[0].id != row.id:
                        counter = splits[0]
                        if 'description' in counter:
                            return counter.description
                elif 'splits' in tx and len(tx.splits) > 2:
                    return 'multiple'
            return 'unknow'

        # self.columns['transfered'].getter_data = get_data_transfered
        self.columns['debit'].getter_data = lambda x: x.value if 'value' in x and x.value > 0 else None
        self.columns['credit'].getter_data = lambda x: -x.value if 'value' in x and x.value < 0 else None

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, account):
        self._account = account
        if account is not None:
            # c = d1.kristine.transaction.find({'splits.account.id': account.id},
            #                                  {'_id': False, 'datetime': True, 'splits': True, 'id': True})
            nature = 'debitable'
            self.account.nature = nature
            from katherine import d6_config
            import pymysql
            d6 = pymysql.connect(**d6_config)
            d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
            d6_cursor.execute('select id, tx_id, datetime, description, num, value from kristine.split '
                              'where account_id = %s order by datetime desc;', (account.id,))

            splits = [Dict(split) for split in d6_cursor]
            balance = Decimal()
            for split in reversed(splits):
                if 'value' in split:
                    if nature == 'debitable':
                        balance += split.value
                    else:
                        balance -= split.value

                split.balance = balance

            self.datasource = splits
            d6_cursor.close()
            d6.close()
        else:
            self.datasource = None
        # self.with_new_empty_row = account is not None


class Splits_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = QMenu(self)
                a = menu.addAction('view transaction')
                def h():
                    row = self.model.datasource[index.row()]
                    from katherine import d1
                    tx = d1.kristine.transaction.find_one({'id': row.tx_id}, {'_id': False})
                    if tx is not None:
                        from isis.kristine.viewer_transaction import Viewer_Transaction
                        vv = Viewer_Transaction()
                        vv.transaction = tx
                        vv.show()

                a.triggered.connect(h)
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class Splits(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.setWindowTitle(self.__class__.__name__)
        self.resize(800, 500)
        self._account = None
        from isis.kristine.widget_account import Widget_Account
        self.viewer_account = Widget_Account(self)
        self.tableview = Splits_Table_View(self)
        layout_main = QVBoxLayout(self)
        layout_main.addWidget(self.viewer_account)
        layout_main.addWidget(self.tableview)
        self.layout = layout_main
        self.model = Splits_Model()
        self.tableview.model = self.model
        self._account = None
        self.account = None

    @property
    def account(self):
        return self.viewer_account.account

    @account.setter
    def account(self, account):
        self.model.account = account
        self.viewer_account.account = account

if __name__ == '__main__':
    from PySide.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    vv = Splits()
    vv.account = Dict({'id': '100-11'})
    vv.show()
    sys.exit(app.exec_())
