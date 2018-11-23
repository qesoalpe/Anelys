from isis.widget import Widget
from isis.table_view import Table_View
from isis.data_model.table import Table
from isis.label import Label
from isis.line_edit import Line_Edit
from PySide.QtGui import QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from decimal import Decimal
from isis.datetime_edit import Datetime_Edit
from datetime import datetime
from PySide.QtCore import Qt
from isis.dialog import Dialog


class swaper():
    def __init__(self, kword, datasource):
        self.kword = kword
        self.ds = datasource

    def __call__(self, i, value):
        if isinstance(self.ds, Table):
            item = self.ds.datasource[i]
        else:
            item = self.ds[i]
        if value is not None and value:
            item[self.kword] = value
        elif self.kword in item:
            del item[self.kword]
        return True


class Splits_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('account', str)
        self.columns.add('datetime', str)
        self.columns.add('num', int)
        self.columns.add('description', str)
        self.columns.add('debit', Decimal, 'c')
        self.columns.add('credit', Decimal, 'c')
        self.with_new_empty_row = False
        self.parent_gui = None

        def get_account(row):
            if 'account' in row:
                account = row.account
                # if 'name' in account:
                #     return account.name
                if 'fullpath' in account:
                    return account.fullpath
                elif 'id' in account:
                    return account.id

        self.columns['account'].getter_data = get_account
        self.columns['debit'].getter_data = lambda x: x.value if 'value' in x and x.value > 0 else None
        self.columns['credit'].getter_data = lambda x: -x.value if 'value' in x and x.value < 0 else None

        self.columns['account'].changing_value = self.handle_changing_account
        self.columns['datetime'].changing_value = swaper('datetime', self)
        self.columns['num'].changing_value = swaper('num', self)
        self.columns['description'].changing_value = swaper('description', self)
        self.columns['debit'].changing_value = self.handle_changing_debit
        self.columns['credit'].changing_value = self.handle_changing_credit

        self.with_new_empty_row = False
        self.after_changing_value.suscribe(self.handle_after_changing_value)
        # self.rowsInserted.connect(self.update_all)
        if not self.has_empty() and not self.has_descuadre(): self.add_row()

    def is_empty(self, row):
        if 'account' not in row and 'value' not in row:
            return True
        else:
            return False

    def has_empty(self):
        for data in self.datasource:
            if 'account' not in data and 'value' not in data:
                return True
        else:
            return False

    def has_descuadre(self):
        for data in self.datasource:
            if 'descuadre' in data:
                return True
        else:
            return False

    def handle_before_changing_value(self, i, *args):
        pass

    def handle_after_changing_value(self, i, c, *args):
        def is_empty(row):
            return 'account' not in row

        i = self.datasource[i]

        if 'descuadre' in i and 'account' in i:
            del i.descuadre

        from functools import reduce
        total = reduce(lambda x, y: x + y.value, list(filter(lambda x: 'value' in x and 'descuadre' not in x, self.datasource)), 0)
        from utils import find_one
        from dict import Dict

        if total != 0:
            descuadre = find_one(lambda x: 'descuadre' in x, self.datasource)
            if descuadre is None:
                descuadre = Dict({'descuadre': True})
            else:
                if self.datasource.index(descuadre) != len(self.datasource) -1:
                    self.remove_row(descuadre)
            descuadre.value = - total
            if descuadre not in self.datasource:
                empty = find_one(self.is_empty, self.datasource)
                if empty is not None:
                    index = self.datasource.index(empty)
                    self.datasource[index] = descuadre
                    self.notify_row_changed(index)
                else:
                    self.add_row(descuadre)
        else:
            descuadre = find_one(lambda x: 'descuadre' in x, self.datasource)
            if descuadre is not None:
                self.remove_row(descuadre)

        if not self.has_empty() and not self.has_descuadre(): self.add_row()

    def total(self):
        total = Decimal()
        for split in self.datasource:
            if 'value' in split:
                total += split.value
        return total

    def handle_changing_account(self, i, value):
        i = self.datasource[i]
        if value is not None and value:
            if 'account' in i and i.account.name == 'value':
                return
            from isis.kristine.search_account import Search_Account
            searcher = Search_Account(self.parent_gui)
            result = searcher.search(value)
            if result is not None:
                i.account = result
            else:
                return False
        elif 'account' in i:
            del i.account
        else:
            return False

    def handle_changing_debit(self, i, value):
        i = self.datasource[i]
        if value is not None and value:
            if 'value' not in i or i.value == 0:
                i.value = value
            elif i.value > 0:
                i.value = value
            elif i.value < 0:
                i.value += value
        elif 'value' in i and i.value > 0:
            del i.value
        else:
            return False

    def handle_changing_credit(self, i, value):
        i = self.datasource[i]
        if value is not None and value:
            if 'value' not in i or i.value == 0:
                i.value = -value
            elif i.value > 0:
                i.value -= value
            elif i.value < 0:
                i.value = -value
        elif 'value' in i and i.value < 0:
            del i.value
        else:
            return False


class Create_Transaction(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(800, 500)
        self.setWindowTitle('Create_Transaction')
        self.close_with_escape = False

        lbl_datetime = Label('datetime: ', self)
        lbl_description = Label('description: ', self)
        lbl_num = Label('num: ', self)
        lbl_datetime.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()
        lbl_num.fix_size_based_on_font()

        self.txt_description = Line_Edit(self)
        self.datetime_edit = Datetime_Edit(self)
        self.txt_num = Line_Edit(self)

        self.tableview = Table_View(self)
        self.tableview.setSelectionMode(self.tableview.SingleSelection)
        self.tableview.setSelectionBehavior(self.tableview.SelectItems)
        self.model = Splits_Model()
        self.model.parent_gui = self
        self.tableview.model = self.model

        btn_create = QPushButton('create', self)
        btn_close = QPushButton('close', self)

        layout_main = QVBoxLayout(self)
        layout_header = QGridLayout()
        layout_header.addWidget(lbl_datetime, 0, 0)
        layout_header.addWidget(self.datetime_edit, 0, 1)
        layout_header.addWidget(lbl_num, 0, 2)
        layout_header.addWidget(self.txt_num, 0, 3)
        layout_header.addWidget(lbl_description, 1, 0)
        layout_header.addWidget(self.txt_description, 1, 1, 1, -1)
        layout_main.addLayout(layout_header)

        layout_main.addWidget(self.tableview)
        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        layout_buttons.addWidget(btn_create)
        layout_buttons.addWidget(btn_close)
        layout_main.addLayout(layout_buttons)
        self.layout = layout_main
        self.datetime_edit.value = datetime.now()

        btn_create.clicked.connect(self.handle_btn_accept_clicked)
        btn_close.clicked.connect(self.close)

    def handle_btn_accept_clicked(self):
        from dict import Dict
        from isodate import datetime_isoformat
        tx = Dict()
        tx.datetime = datetime_isoformat(self.datetime_edit.value)
        if self.txt_num.text:
            tx.num = self.txt_num.txt
            if not isinstance(tx.num , int):
                try:
                    tx.num = int(tx.num)
                except:
                    if 'num' in tx:
                        del tx.num
        if self.txt_description.text:
            tx.description = self.txt_description.text
        from copy import deepcopy
        splits = deepcopy(self.model.datasource)
        for split in splits[:]:
            if 'account' not in split or 'value' not in split:
                splits.remove(split)
        tx.splits = splits

        from sarah.acp_bson import Client
        agent_kristine = Client('', 'kristine')
        msg = Dict({'type_message': 'action', 'action': 'kristine/create_transaction', 'transaction': tx})
        answer = agent_kristine(msg)
        if 'transaction' in answer:
            QMessageBox.information(self, 'success', 'transaction created successfully')
            self.close()
            return
        else:
            QMessageBox.warning(self, 'error', 'an error has happened')
            return


if __name__ == '__main__':
    from PySide.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    vv = Create_Transaction()
    vv.show()
    sys.exit(app.exec_())
