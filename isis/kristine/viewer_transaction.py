from isis.dialog import Dialog
from isis.data_model.table import Table
from isis.table_view import Table_View
from decimal import Decimal
from isis.label import Label
from PySide.QtGui import QGridLayout


class Model_Splits(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('datetime', str)
        self.columns.add('num', int)
        self.columns.add('description', str)
        self.columns.add('account', str)
        self.columns.add('debit', Decimal, 'c')
        self.columns.add('credit', Decimal, 'c')
        # self.columns.add('balance', Decimal, 'c')
        self.with_new_empty_row = False
        self.readonly = True

        self.columns['debit'].getter_data = lambda x: x.value if 'value' in x and x.value > 0 else None
        self.columns['credit'].getter_data = lambda x: -x.value if 'value' in x and x.value < 0 else None

        def h(x):
            if 'account' in x:
                account = x.account
                if 'fullpath' in account:
                    return account.fullpath
                elif 'id' in account:
                    from kristine.repository import accounts
                    from utils import find_one
                    _account = find_one(lambda x: x.id == account.id, accounts)
                    if _account is not None and 'fullpath' in _account:
                        return _account.fullpath
                    return account.id

        self.columns['account'].getter_data = h

    @property
    def splits(self):
        return self.datasource

    @splits.setter
    def splits(self, splits):
        self.datasource = splits


class Split_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectItems)


class Viewer_Transaction(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.setWindowTitle(self.__class__.__name__)
        self.resize(700, 500)
        lbl_id = Label('id: ', self)
        lbl_datetime = Label('datetime: ', self)
        lbl_description = Label('description: ', self)
        self.lbl_id = Label(self)
        self.lbl_datetime = Label(self)
        self.lbl_description = Label(self)

        lbl_id.fix_size_based_on_font()
        lbl_datetime.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()

        self.tableview = Split_Table_View(self)

        layout_main = QGridLayout(self)
        layout_main.addWidget(lbl_id, 0, 0)
        layout_main.addWidget(self.lbl_id, 0, 1)
        layout_main.addWidget(lbl_datetime, 0, 2)
        layout_main.addWidget(self.lbl_datetime, 0, 3)
        layout_main.addWidget(lbl_description, 1, 0)
        layout_main.addWidget(self.lbl_description, 1, 1, 1, -1)
        layout_main.addWidget(self.tableview, 2, 0, 1, -1)

        self.layout = layout_main
        self.model = Model_Splits()
        self.tableview.model = self.model

        self._transaction = None

    @property
    def transaction(self):
        return self._transaction

    @transaction.setter
    def transaction(self, tx):
        self._transaction = tx
        if tx is not None:
            self.lbl_id.text = tx.id if 'id' in tx else None
            self.lbl_datetime.text = tx.datetime if 'datetime' in tx else None
            self.lbl_description.text = tx.description if 'description' in tx else None
            self.model.datasource = tx.splits if 'splits' in tx else None
        else:
            self.lbl_id.text = None
            self.lbl_datetime.text = None
            self.lbl_description.text = None
            self.model.datasource = None


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Viewer_Transaction()
    from katherine import d1
    tx = d1.kristine.transaction.find_one({'id': 'kristine_transaction-18'}, {'_id': False})
    vv.transaction = tx
    vv.show()
    sys.exit(app.exec_())
