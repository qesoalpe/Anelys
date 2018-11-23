from copy import deepcopy
from sarah.acp_bson import Client
from PySide.QtCore import *
from PySide.QtGui import *
from babel.numbers import format_currency
from decimal import Decimal
import datetime
import isodate


def setfixedwidth(ww):
    ww.setFixedWidth(ww.fontMetrics().width(ww.text()))


class Model_Debts(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None

    def rowCount(self, parent=None):
        if self._datasource is not None and isinstance(self._datasource, list):
            return len(self._datasource)
        else:
            return 0

    def columnCount(self, parent=None):
        return 6

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.COLUMN_ID:
                return 'id'
            elif section == self.COLUMN_FOLIO:
                return 'folio'
            elif section == self.COLUMN_EXPIRES:
                return 'expires'
            elif section == self.COLUMN_BALANCE:
                return 'balance'
            elif section == self.COLUMN_PAYMENT:
                return 'payment'
            elif section == self.COLUMN_REMAINS:
                return 'remains'

    @property
    def datasource(self):
        return self._datasource

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_ID:
                if 'id' in data:
                    return data['id']
            elif index.column() == self.COLUMN_FOLIO:
                if 'folio' in data:
                    return data['folio']
            elif index.column() == self.COLUMN_EXPIRES:
                if 'expires' in data:
                    return data['expires']
            elif index.column() == self.COLUMN_BALANCE:
                if 'balance' in data:
                    return format_currency(data['balance'], 'MXN', locale='es_mx')
            elif index.column() == self.COLUMN_PAYMENT:
                if 'payment' in data:
                    return format_currency(data['payment'], 'MXN', locale='es_mx')
            elif index.column() == self.COLUMN_REMAINS:
                if 'remains' in data:
                    return format_currency(data['remains'], 'MXN', locale='es_mx')

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    COLUMN_ID = 0
    COLUMN_FOLIO = 1
    COLUMN_EXPIRES = 2
    COLUMN_BALANCE = 3
    COLUMN_PAYMENT = 4
    COLUMN_REMAINS = 5


class Table_View_Debts(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model):
        QTableView.setModel(self, model)

        def handle_changes_in_model(*args):
            self.resizeColumnsToContents()

        model.dataChanged.connect(handle_changes_in_model)
        model.modelReset.connect(handle_changes_in_model)
        model.rowsInserted.connect(handle_changes_in_model)
        model.rowsRemoved.connect(handle_changes_in_model)


class Creater_Receipt(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.resize(400, 500)
        self.setWindowTitle('Creater_Receipt')

        lbl_balance = QLabel('balance: ', self)
        lbl_amount = QLabel('amount: ', self)
        lbl_remains = QLabel('remains: ', self)

        self.lbl_balance = QLabel(self)
        self.spn_amount = QDoubleSpinBox(self)
        self.lbl_remains = QLabel(self)

        self.tableviewdebts = Table_View_Debts(self)

        btn_create = QPushButton('create', self)
        btn_close = QPushButton('close', self)

        layoutmain = QGridLayout()

        setfixedwidth(lbl_balance)
        setfixedwidth(lbl_amount)
        setfixedwidth(lbl_remains)

        layoutmain.addWidget(lbl_balance, 0, 0)
        layoutmain.addWidget(self.lbl_balance, 0, 1)
        layoutmain.addWidget(lbl_remains, 1, 0)
        layoutmain.addWidget(self.lbl_remains, 1, 1)
        layoutmain.addWidget(lbl_amount, 0, 2)
        layoutmain.addWidget(self.spn_amount, 0, 3)
        layoutmain.addWidget(self.tableviewdebts, 2, 0, 1, -1)

        buttonslayout = QHBoxLayout()
        buttonslayout.addStretch()
        buttonslayout.addWidget(btn_create)
        buttonslayout.addWidget(btn_close)

        layoutmain.addItem(buttonslayout, 3, 0, 1, -1)

        self.setLayout(layoutmain)
        self.spn_amount.valueChanged.connect(self.handle_spn_amount_value_changed)
        btn_create.clicked.connect(self.handle_btn_create_clicked)
        btn_close.clicked.connect(self.close)
        self.modeldebts = Model_Debts(self)
        self.tableviewdebts.setModel(self.modeldebts)
        self.amount = None
        self.receipt = None
        self._debts = None
        self._account = None
        self._balance = None
        self.agent_caroline = Client('Creater_Receipt', 'caroline')

    @property
    def debts(self):
        return self._debts

    @debts.setter
    def debts(self, x):
        x = deepcopy(x)
        debts = list()
        for debt in x:
            if 'status' in debt and debt['status'] == 'valid':
                debts.append(debt)
                debt['remains'] = debt['balance']
                if 'payment' in debt:
                    del debt['payment']
                elif 'payments' in debt:
                    del debt['payments']

        x = debts
        debts = list()

        for debt in x[:]:
            if 'debt_type' not in debt:
                debts.append(debt)
                x.remove(debt)

        for debt in x[:]:
            debts.append(debt)
            x.remove(debt)

        balance = Decimal()
        for debt in debts:
            balance += debt['balance']
        self.spn_amount.setMaximum(balance)
        self.lbl_balance.setText(format_currency(balance, 'MXN', locale='es_mx'))
        self.lbl_remains.setText(format_currency(balance, 'MXN', locale='es_mx'))
        self._debts = debts
        self._balance = balance
        self.modeldebts.datasource = self._debts
        self.spn_amount.setValue(balance)

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, x):
        self._account = x

    def handle_spn_amount_value_changed(self, value):
        remanent = round(Decimal(value), 2)
        value = round(Decimal(value), 2)

        for debt in self.debts:
            if remanent > 0:
                if remanent > debt['balance']:
                    debt['payment'] = debt['balance']
                    debt['remains'] = 0
                else:
                    debt['payment'] = remanent
                    debt['remains'] = debt['balance'] - debt['payment']
                remanent -= debt['payment']
            else:
                if 'payment' in debt:
                    del debt['payment']
                debt['remains'] = debt['balance']
        self.lbl_remains.setText(format_currency(self._balance - value, 'MXN', locale='es_mx'))
        self.modeldebts.modelReset.emit()

    def handle_btn_create_clicked(self):
        receipt = dict()
        receipt['amount'] = round(Decimal(self.spn_amount.value()), 2)
        receipt['datetime'] = isodate.datetime_isoformat(datetime.datetime.now())
        debited = list()
        for debt in self.debts:
            if 'payment' in debt:
                debited.append({'id': debt['id'], 'type': debt['type'], 'value': debt['payment']})
        if len(debited) == 1:
            receipt['debited'] = debited[0]
        elif len(debited) > 1:
            receipt['debited'] = debited
        # receipt['account'] = self.account
        msg = {'type_message': 'action', 'action': 'caroline/create_receipt', 'receipt': receipt}
        answer = self.agent_caroline(msg)
        if 'error' in answer and answer['error']:
            QMessageBox.warning(self, 'error', 'an error has happened')
            return
        else:
            self.receipt = answer['receipt']
            self.close()
