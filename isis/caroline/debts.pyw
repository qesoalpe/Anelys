from isis.caroline.search_account import Search_Account
from PySide.QtGui import *
from PySide.QtCore import *
from babel.numbers import format_currency
from sarah.acp_bson import Client
from decimal import Decimal
import json
import datetime
from isodate import parse_duration, datetime_isoformat
from isis.caroline.creater_receipt import Creater_Receipt


def setfixedwidth(ww):
    ww.setFixedWidth(ww.fontMetrics().width(ww.text()))


class Viewer_Debt(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Viewer_Debt')
        self.resize(500, 300)
        self.txt_debt = QTextEdit(self)
        self.txt_debt.setReadOnly(True)
        layoutmain = QVBoxLayout(self)
        layoutmain.addWidget(self.txt_debt)
        self.setLayout(layoutmain)
        self._debt = None
        self.update_ui()

    def update_ui(self):
        if self._debt is not None:
            from sarah.dictutils import dec_to_float, float_to_dec
            dec_to_float(self._debt)
            self.txt_debt.setText(json.dumps(self._debt, indent=2))
            float_to_dec(self._debt)
        else:
            self.txt_debt.setText('')

    @property
    def debt(self):
        return self._debt

    @debt.setter
    def debt(self, x):
        self._debt = x
        self.update_ui()


class Register_Payment(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        lbl_debt = QLabel('debt', self)
        lbl_debt_id = QLabel('id: ', self)
        lbl_debt_folio = QLabel('folio: ', self)
        lbl_debt_balance = QLabel('balance: ', self)
        lbl_payment = QLabel('payment', self)
        lbl_payment_value = QLabel('value: ', self)
        lbl_payment_comments = QLabel('comments: ', self)
        self.lbl_debt_id = QLabel(self)
        self.lbl_debt_folio = QLabel(self)
        self.lbl_debt_balance = QLabel(self)
        self.spn_payment_value = QDoubleSpinBox(self)
        self.txt_payment_comments = QTextEdit(self)
        btn_register = QPushButton('register', self)
        btn_close = QPushButton('close', self)
        setfixedwidth(lbl_debt_id)
        setfixedwidth(lbl_debt_folio)
        setfixedwidth(lbl_payment_value)
        self.spn_payment_value.setPrefix('$')
        layoutmain = QGridLayout(self)
        layoutmain.addWidget(lbl_debt, 0, 0)
        layoutmain.addWidget(lbl_debt_id, 1, 0)
        layoutmain.addWidget(self.lbl_debt_id, 1, 1)
        layoutmain.addWidget(lbl_debt_folio, 2, 0)
        layoutmain.addWidget(self.lbl_debt_folio, 2, 1)
        layoutmain.addWidget(lbl_debt_balance, 3, 0)
        layoutmain.addWidget(self.lbl_debt_balance, 3, 1)
        layoutmain.addWidget(lbl_payment, 4, 0)
        layoutmain.addWidget(lbl_payment_value, 5, 0)
        layoutmain.addWidget(self.spn_payment_value, 5, 1)
        layoutmain.addWidget(lbl_payment_comments, 6, 0)
        layoutmain.addWidget(self.txt_payment_comments, 6, 1)
        layoutmain.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 7, 0, 1, -1)
        layoutmain.addWidget(btn_register, 8, 0)
        layoutmain.addWidget(btn_close, 8, 1)
        self.setLayout(layoutmain)
        btn_register.clicked.connect(self.handle_btn_register_clicked)
        btn_close.clicked.connect(self.close)

        self.debt = None
        self.account = None
        self.agent_caroline = None
        self.update_ui()

    def showEvent(self, *args, **kwargs):
        self.update_ui()

    def update_ui(self):
        if self.debt is not None:
            if 'id' in self.debt:
                self.lbl_debt_id.setText(self.debt['id'])
            else:
                self.lbl_debt_id.setText('')
            if 'folio' in self.debt:
                self.lbl_debt_folio.setText(self.debt['folio'])
            else:
                self.lbl_debt_folio.setText('')
            if 'balance' in self.debt:
                self.spn_payment_value.setMaximum(self.debt['balance'])
                self.spn_payment_value.setValue(self.debt['balance'])
                self.lbl_debt_balance.setText(format_currency(self.debt['balance'], 'MXN', locale='es_mx'))
            else:
                self.spn_payment_value.setMaximum(1000000000)
                self.spn_payment_value.setValue(0)
                self.lbl_debt_balance.setText('')
        else:
            self.lbl_debt_id.setText('')
            self.lbl_debt_folio.setText('')
            self.lbl_debt_balance.setText('')
            self.spn_payment_value.setMaximum(1000000000)

    def handle_btn_register_clicked(self):
        if self.debt is None:
            return
        payment = dict()
        payment['datetime'] = datetime_isoformat(datetime.datetime.now())
        payment['value'] = round(Decimal(self.spn_payment_value.value()), 2)
        if self.txt_payment_comments.toPlainText():
            payment['comments'] = self.txt_payment_comments.toPlainText()
        if self.agent_caroline is None:
            self.agent_caroline = Client('isis.caroline.debts.register_payment', 'caroline')
        msg = {'type_message': 'action', 'action': 'caroline/register_payment', 'payment': payment, 'debt': self.debt}
        answer = self.agent_caroline.send_msg(msg)
        if 'error' in answer:
            QMessageBox.warning(self, 'error', 'an error has happened')
        else:
            QMessageBox.information(self, 'success', 'payment has been registered successfully')
            if 'debt' in answer:
                self.debt = answer['debt']
            else:
                self.debt = None
            if 'account' in answer:
                self.account = answer['account']
            else:
                self.account = None
            self.close()


class Create_Debt(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.resize(300, 500)
        self.setWindowTitle('Create_Debt')
        lbl_account = QLabel('account', self)
        lbl_account_id = QLabel('id: ', self)
        lbl_account_type = QLabel('type: ', self)
        lbl_account_name = QLabel('name: ', self)
        lbl_debt = QLabel('debt', self)
        lbl_type = QLabel('type: ', self)
        lbl_folio = QLabel('folio: ', self)
        lbl_datetime = QLabel('datetime', self)
        lbl_expires = QLabel('expires: ', self)
        lbl_amount = QLabel('amount: ', self)
        lbl_comments = QLabel('comments: ', self)
        self.lbl_account_id = QLabel(self)
        self.lbl_account_type = QLabel(self)
        self.lbl_account_name = QLabel(self)
        self.txt_type = QLineEdit(self)
        self.txt_folio = QLineEdit(self)
        self.date_datetime = QDateTimeEdit(self)
        self.date_expires = QDateTimeEdit(self)
        self.spn_amount = QDoubleSpinBox(self)
        self.txt_comments = QTextEdit(self)
        btn_create = QPushButton('create', self)
        btn_close = QPushButton('close', self)

        self.date_datetime.setDateTime(datetime.datetime.now())
        self.date_expires.setDateTime(datetime.datetime.now())
        self.date_expires.setFocusPolicy(Qt.NoFocus)
        self.date_expires.setReadOnly(True)
        self.spn_amount.setPrefix('$')
        self.spn_amount.setMinimum(0)
        self.spn_amount.setMaximum(100000)

        setfixedwidth(lbl_account_id)
        setfixedwidth(lbl_account_type)
        setfixedwidth(lbl_account_name)
        setfixedwidth(lbl_type)
        setfixedwidth(lbl_folio)
        setfixedwidth(lbl_datetime)
        setfixedwidth(lbl_expires)
        setfixedwidth(lbl_amount)
        setfixedwidth(lbl_comments)
        mainlayout = QGridLayout(self)
        mainlayout.addWidget(lbl_account, 0, 0)
        mainlayout.addWidget(lbl_account_id, 1, 0)
        mainlayout.addWidget(self.lbl_account_id, 1, 1)
        mainlayout.addWidget(lbl_account_type, 2, 0)
        mainlayout.addWidget(self.lbl_account_type, 2, 1)
        mainlayout.addWidget(lbl_account_name, 3, 0)
        mainlayout.addWidget(self.lbl_account_name, 3, 1)
        mainlayout.addWidget(lbl_debt, 4, 0)
        mainlayout.addWidget(lbl_type, 5, 0)
        mainlayout.addWidget(self.txt_type, 5, 1)
        mainlayout.addWidget(lbl_folio, 6, 0)
        mainlayout.addWidget(self.txt_folio, 6, 1)
        mainlayout.addWidget(lbl_datetime, 7, 0)
        mainlayout.addWidget(self.date_datetime, 7, 1)
        mainlayout.addWidget(lbl_expires, 8, 0)
        mainlayout.addWidget(self.date_expires, 8, 1)
        mainlayout.addWidget(lbl_amount, 9, 0)
        mainlayout.addWidget(self.spn_amount, 9, 1)
        mainlayout.addWidget(lbl_comments, 10, 0)
        mainlayout.addWidget(self.txt_comments, 10, 1)
        mainlayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 11, 0, 1, -1)
        mainlayout.addWidget(btn_create, 12, 0)
        mainlayout.addWidget(btn_close, 12, 1)
        self.setLayout(mainlayout)
        self._account = None
        self.account = self._account

        btn_close.clicked.connect(self.close)
        self.date_datetime.dateTimeChanged.connect(self.handle_date_datetime_dateTimeChanged)
        btn_create.clicked.connect(self.handle_btn_create_clicked)
        self.agent_caroline = None
        self.debt = None

    def handle_date_datetime_dateTimeChanged(self, date_time):
        date_time = date_time.toPython()
        if self.account is not None:
            if 'credit_period' in self.account:
                if isinstance(self.account['credit_period'], (int, Decimal, float)):
                    self.date_expires.setDateTime(date_time +
                                                  datetime.timedelta(days=int(self.account['credit_period'])))
                elif isinstance(self.account['credit_period'], str):
                    self.date_expires.setDateTime(date_time + parse_duration(self.account['credit_period']))

    def handle_btn_create_clicked(self):
        debt = dict()
        if self.txt_type.text():
            debt['type'] = self.txt_type.text()
        if self.txt_folio.text():
            debt['folio'] = self.txt_folio.text()
        debt['datetime'] = datetime_isoformat(self.date_datetime.dateTime().toPython())
        debt['expires'] = datetime_isoformat(self.date_expires.dateTime().toPython(), '%Y-%m-%d')
        debt['amount'] = round(Decimal(self.spn_amount.value()), 2)
        if self.txt_comments.toPlainText():
            debt['comments'] = self.txt_comments.toPlainText()
        msg = {'type_message': 'action', 'action': 'caroline/create_debt', 'debt': debt, 'account': self.account}
        if self.agent_caroline is None:
            self.agent_caroline = Client('isis.caroline.debts.create_debt', 'caroline')
        answer = self.agent_caroline.send_msg(msg)
        if 'error' not in answer:
            QMessageBox.information(self, 'created', 'the debt has been created successfuly')
            self.debt = answer['debt']
            self.account = answer['account']
            self.close()
        else:
            if 'error_msg' in answer and isinstance(answer['error_msg'], str):
                msg_error = 'an error ocured msg: ' + answer['error_msg']
            else:
                msg_error = 'an erro ocured'
            QMessageBox.warning(self, 'error', msg_error)

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, x):
        self._account = x
        acc = x
        if x is not None:
            if 'id' in acc:
                self.lbl_account_id.setText(acc['id'])
            else:
                self.lbl_account_id.setText('')
            if 'type' in acc:
                self.lbl_account_type.setText(acc['type'])
            else:
                self.lbl_account_type.setText('')
            if 'name' in acc:
                self.lbl_account_name.setText(acc['name'])
            else:
                self.lbl_account_name.setText('')
            if 'credit_period' in acc:
                debt_datetime = self.date_datetime.dateTime().toPython()
                if isinstance(acc['credit_period'], (int, Decimal)):
                    self.date_expires.setDateTime(debt_datetime + datetime.timedelta(days=int(acc['credit_period'])))
                elif isinstance(acc['credit_period'], str):
                    self.date_expires.setDateTime(debt_datetime + parse_duration(acc['credit_period']))
        else:
            self.lbl_account_id.setText('')
            self.lbl_account_type.setText('')
            self.lbl_account_name.setText('')


class Table_Model_Debts(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None

    COLUMN_ID = 0
    COLUMN_TYPE = 1
    COLUMN_FOLIO = 2
    COLUMN_DATETIME = 3
    COLUMN_AMOUNT = 4
    COLUMN_BALANCE = 5
    COLUMN_EXPIRES = 6
    COLUMN_STATUS = 7

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def rowCount(self, parent=None):
        if self.datasource is None:
            return 0
        else:
            return len(self.datasource)

    def columnCount(self, parent=None):
        return 8

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = self.datasource[index.row()]
            if index.column() == Table_Model_Debts.COLUMN_ID:
                if 'id' in row:
                    return row['id']
            elif index.column() == Table_Model_Debts.COLUMN_TYPE:
                if 'type' in row:
                    return row['type']
            elif index.column() == Table_Model_Debts.COLUMN_FOLIO:
                if 'folio' in row:
                    return row['folio']
            elif index.column() == Table_Model_Debts.COLUMN_DATETIME:
                if 'datetime' in row:
                    return row['datetime']
            elif index.column() == Table_Model_Debts.COLUMN_AMOUNT:
                if 'amount' in row:
                    return format_currency(row['amount'], 'MXN', locale='es_MX')
            elif index.column() == Table_Model_Debts.COLUMN_BALANCE:
                if 'balance' in row:
                    return format_currency(row['balance'], 'MXN', locale='es_MX')
            elif index.column() == Table_Model_Debts.COLUMN_EXPIRES:
                if 'expires' in row:
                    return row['expires']
            elif index.column() == Table_Model_Debts.COLUMN_STATUS:
                if 'status' in row:
                    return row['status']

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == Table_Model_Debts.COLUMN_ID:
                return 'id'
            elif section == Table_Model_Debts.COLUMN_TYPE:
                return 'type'
            elif section == Table_Model_Debts.COLUMN_FOLIO:
                return 'folio'
            elif section == Table_Model_Debts.COLUMN_DATETIME:
                return 'datetime'
            elif section == Table_Model_Debts.COLUMN_AMOUNT:
                return 'amount'
            elif section == Table_Model_Debts.COLUMN_BALANCE:
                return 'balance'
            elif section == Table_Model_Debts.COLUMN_EXPIRES:
                return 'expires'
            elif section == Table_Model_Debts.COLUMN_STATUS:
                return 'status'

    def item_updated(self, index):
        topleft = self.index(index, 0)
        bottomright = self.index(index, self.columnCount() - 1)
        self.dataChanged.emit(topleft, bottomright)


class Table_View_Debts(QTableView):
    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.handler_action_register_payment = None
        self.handler_view = None

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.modelReset.connect(self.resizeColumnsToContents)

    def mouseDoubleClickEvent(self, event):
        QTableView.mouseDoubleClickEvent(self, event)
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                if self.handler_view is not None:
                    self.handler_view(index.row())

    def mousePressEvent(self, event):
        QTableView.mousePressEvent(self, event)
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = QMenu(self)
                register_payment = menu.addAction('register payment')
                view = menu.addAction('view')

                def reg_payment():
                    if self.handler_action_register_payment is not None:
                        self.handler_action_register_payment(index.row())

                def handle_view():
                    if self.handler_view is not None:
                        self.handler_view(index.row())

                register_payment.triggered.connect(reg_payment)
                view.triggered.connect(handle_view)
                menu.popup(event.globalPos())

                # register_payment.triggered.connect()
            # if index.isValid() and self.handle_clicked_right_over_debt is not None:
            #   self.handle_clicked_rigth_over_debt()


class Central_Widget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        lbl_account = QLabel('account', self)
        btn_change_account = QPushButton('change account', self)
        lbl_account_id = QLabel('id: ', self)
        lbl_account_name = QLabel('name: ', self)
        lbl_account_balance = QLabel('balance: ', self)
        lbl_account_balance_in_hand = QLabel('balance in hand: ', self)
        self.lbl_account_id = QLabel(self)
        self.lbl_account_name = QLabel(self)
        self.lbl_account_balance = QLabel(self)
        self.lbl_account_balance_in_hand = QLabel(self)
        setfixedwidth(lbl_account_id)
        setfixedwidth(lbl_account_name)
        setfixedwidth(lbl_account_balance)
        setfixedwidth(lbl_account_balance_in_hand)
        self.tableviewdebts = Table_View_Debts(self)
        self.tablemodeldebts = Table_Model_Debts(self)
        self.tableviewdebts.setModel(self.tablemodeldebts)

        btn_create_debt = QPushButton('create', self)
        btn_view = QPushButton('view', self)
        btn_create_receipt = QPushButton('create_receipt', self)
        layoutaccount = QGridLayout()
        layoutaccount.addWidget(lbl_account, 0, 0)
        layoutaccount.addWidget(btn_change_account, 0, 3, Qt.AlignRight)
        layoutaccount.addWidget(lbl_account_id, 1, 0)
        layoutaccount.addWidget(self.lbl_account_id, 1, 1)
        layoutaccount.addWidget(lbl_account_name, 2, 0)
        layoutaccount.addWidget(self.lbl_account_name, 2, 1)
        layoutaccount.addWidget(lbl_account_balance, 1, 2)
        layoutaccount.addWidget(self.lbl_account_balance, 1, 3)
        layoutaccount.addWidget(lbl_account_balance_in_hand, 2, 2)
        layoutaccount.addWidget(self.lbl_account_balance_in_hand, 2, 3)

        layoutbuttonsdebt = QHBoxLayout()
        layoutbuttonsdebt.addWidget(btn_create_debt)
        layoutbuttonsdebt.addWidget(btn_view)
        layoutbuttonsdebt.addWidget(btn_create_receipt)
        layoutbuttonsdebt.addStretch()

        mainlayout = QVBoxLayout(self)
        mainlayout.addItem(layoutaccount)
        mainlayout.addItem(layoutbuttonsdebt)
        mainlayout.addWidget(self.tableviewdebts)
        self.setLayout(mainlayout)
        btn_change_account.clicked.connect(self.handle_btn_change_account_clicked)
        btn_create_debt.clicked.connect(self.handle_btn_create_debt_clicked)
        btn_view.clicked.connect(self.handle_btn_view_clicked)
        btn_create_receipt.clicked.connect(self.handle_btn_create_receipt_clicked)
        self.tableviewdebts.handler_action_register_payment = self.handle_table_view_register_payment
        self.tableviewdebts.handler_view = self.handle_table_view_view
        self.agent_caroline = None
        self._account = None
        self._debts = None
        self.account = self._account

    def handle_btn_change_account_clicked(self):
        searcher = Search_Account(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.account = searcher.selected

    def handle_btn_create_debt_clicked(self):
        if self.account is not None:
            dialog = Create_Debt(self)
            dialog.account = self.account
            dialog.exec_()
            if dialog.account is not None and dialog.debt is not None:
                self.account = dialog.account

    def handle_btn_view_clicked(self):
        index = self.tableviewdebts.currentIndex()
        if index.isValid():
            viewer = Viewer_Debt(self)
            viewer.debt = self.debts[index.row()]
            viewer.show()

    def handle_btn_create_receipt_clicked(self):
        creater = Creater_Receipt(self)
        creater.debts = self.debts
        creater.exec_()
        if creater.receipt is not None:
            msg = {'type_message': 'find_one', 'type': self.account['type'], 'query': {'id': self.account['id']}}
            answer = self.agent_caroline(msg)
            self.account = answer['result']

    def handle_table_view_register_payment(self, index):
        debt = self.debts[index]
        registrador = Register_Payment(self)
        registrador.debt = debt
        registrador.exec_()
        if registrador.debt is not None:
            self.debts[index] = registrador.debt
            self.tablemodeldebts.item_updated(index)
        if registrador.account is not None:
            self._account = registrador.account
            self.update_account_ui()

    def handle_table_view_view(self, index):
        viewer = Viewer_Debt(self)
        viewer.debt = self.debts[index]
        viewer.show()

    def update_account_ui(self):
        account = self._account
        if account is not None:
            if 'id' in account:
                self.lbl_account_id.setText(account['id'])
            else:
                self.lbl_account_id.setText('')
            if 'name' in account:
                self.lbl_account_name.setText(account['name'])
            else:
                self.lbl_account_name.setText('')
            if 'balance' in self.account:
                self.lbl_account_balance.setText(format_currency(self.account['balance'], 'MXN', locale='es_mx'))
            else:
                self.lbl_account_balance.setText('')
            if 'balance_in_hand' in self.account:
                self.lbl_account_balance_in_hand.setText(
                    format_currency(self.account['balance_in_hand'], 'MXN', locale='es_MX'))
            else:
                self.lbl_account_balance_in_hand.setText('')
        else:
            self.lbl_account_id.setText('')
            self.lbl_account_name.setText('')
            self.lbl_account_balance.setText('')
            self.lbl_account_balance_in_hand.setText('')

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, x):
        self._account = x
        account = self._account
        if account is not None:
            if self.agent_caroline is None:
                self.agent_caroline = Client('isis.caroline.debts', 'caroline')
            if 'balance' not in account:
                msg = {'type_message': 'request', 'request_type': 'get', 'get': 'caroline/account_balance',
                       'account': account}
                answer = self.agent_caroline.send_msg(msg)
                if 'balance' in answer:
                    account['balance'] = answer['balance']
                if 'balance_in_hand' in answer:
                    account['balance_in_hand'] = answer['balance_in_hand']
            if 'id' in account:
                self.lbl_account_id.setText(account['id'])
            else:
                self.lbl_account_id.setText('')
            if 'name' in account:
                self.lbl_account_name.setText(account['name'])
            else:
                self.lbl_account_name.setText('')
            msg = {'type_message': 'find', 'type': 'caroline/debt', 'query': {'account': account, 'status': 'valid'}}
            answer = self.agent_caroline.send_msg(msg)
            self.debts = answer['result']
            if 'balance' in self.account:
                self.lbl_account_balance.setText(format_currency(self.account['balance'], 'MXN', locale='es_mx'))
            else:
                self.lbl_account_balance.setText('')
            if 'balance_in_hand' in self.account:
                self.lbl_account_balance_in_hand.setText(
                    format_currency(self.account['balance_in_hand'], 'MXN', locale='es_MX'))
            else:
                self.lbl_account_balance_in_hand.setText('')
        else:
            self.lbl_account_id.setText('')
            self.lbl_account_name.setText('')
            self.lbl_account_balance.setText('')
            self.lbl_account_balance_in_hand.setText('')
            self.debts = None

    @property
    def debts(self):
        return self._debts

    @debts.setter
    def debts(self, x):
        self._debts = x
        self.tablemodeldebts.datasource = self.debts


class Debts(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 600)
        self.setWindowTitle('Debts')
        self.cwidget = Central_Widget(self)
        self.setCentralWidget(self.cwidget)

    @property
    def account(self):
        return None

    @account.setter
    def account(self, x):
        self.cwidget.account = x


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Debts()
    # agent_caroline = Client('alejandro', 'caroline')
    # msg = {'type_message': 'find_one', 'type': 'caroline/account', 'query': {'id': '3-19'}}
    # answer = agent_caroline.send_msg(msg)
    # vv.account = answer['result']
    vv.show()
    sys.exit(app.exec_())
