from babel.numbers import format_currency
from decimal import Decimal
from sarah.acp_bson import Client
from isis.dialog import Dialog
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout
from isis.message_box import Message_Box
from isis.main_window import Main_Window
from isis.h_box_layout import H_Box_Layout
from dict import Dict as dict


class Charger(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        lbl_number = Label('number: ', self)
        lbl_amount = Label('amount: ', self)
        lbl_account = Label('account: ', self)
        lbl_bank = Label('bank: ', self)
        self.lbl_number = Label(self)
        self.lbl_amount = Label(self)
        self.lbl_account = Label(self)
        self.lbl_bank = Label(self)

        lbl_charge = Label('charge', self)
        lbl_date = Label('datetime', self)
        lbl_mov_number = Label('mov_number', self)
        lbl_description = Label('description: ', self)

        self.txt_date = Line_Edit(self)
        self.txt_mov_number = Line_Edit(self)
        self.txt_description = Line_Edit(self)

        btn_charge = Push_Button('charge', self)
        btn_close = Push_Button('close', self)

        lbl_number.fix_size_based_on_font()
        lbl_amount.fix_size_based_on_font()
        lbl_account.fix_size_based_on_font()
        lbl_bank.fix_size_based_on_font()
        lbl_charge.fix_size_based_on_font()
        lbl_date.fix_size_based_on_font()
        lbl_mov_number.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()

        layoutmain = Grid_Layout()
        layoutmain.addWidget(lbl_number, 0, 0)
        layoutmain.addWidget(self.lbl_number, 0, 1)
        layoutmain.addWidget(lbl_amount, 0, 2)
        layoutmain.addWidget(self.lbl_amount, 0, 3)
        layoutmain.addWidget(lbl_account, 1, 0)
        layoutmain.addWidget(self.lbl_account, 1, 1)
        layoutmain.addWidget(lbl_bank, 2, 0)
        layoutmain.addWidget(self.lbl_bank, 2, 1)
        layoutmain.addWidget(lbl_charge, 3, 0)
        layoutmain.addWidget(lbl_date, 4, 0)
        layoutmain.addWidget(self.txt_date, 4, 1)
        layoutmain.addWidget(lbl_mov_number, 4, 2)
        layoutmain.addWidget(self.txt_mov_number, 4, 3)
        layoutmain.addWidget(lbl_description, 5, 0)
        layoutmain.addWidget(self.txt_description, 5, 1, 1, -1)

        buttonslayout = H_Box_Layout()
        buttonslayout.addStretch()
        buttonslayout.addWidget(btn_charge)
        buttonslayout.addWidget(btn_close)
        layoutmain.addItem(buttonslayout, 6, 0, 1, -1)

        self.setLayout(layoutmain)

        self._check = None
        self._account = None
        self._bank = None
        self.transaction = None
        btn_charge.clicked.connect(self.handle_btn_charge_clicked)
        btn_close.clicked.connect(self.close)
        self.agent_bailey = Client('Charger', 'bailey')

    def handle_btn_charge_clicked(self):
        if self.check is None or self.account is None or self.bank is None is None:
            Message_Box.warning(self, 'invalid', 'is needed check account and bank to charge the check')
            return
        trans = dict()
        trans['mov_num'] = int(self.txt_mov_number.text)
        trans['description'] = self.txt_description.text
        trans['date'] = self.txt_date.text
        trans['value'] = - self.check['amount']
        msg = {'type_message': 'action', 'action': 'bailey/charge_check', 'check': self.check, 'account': self.account,
               'bank': self.bank, 'transaction': trans}
        answer = self.agent_bailey(msg)
        if 'error' in answer and answer['error']:
            Message_Box.warning(self, 'error', 'may be some error happened in the transaction or some where')
            return
        else:
            self.transaction = answer['transaction']
            self.check = answer['check']
            Message_Box.information(self, 'success', 'the check has been charged')
            self.close()

    @property
    def check(self):
        return self._check

    @check.setter
    def check(self, x):
        self._check = x
        check = self._check
        if check is not None:
            if 'number' in check:
                self.lbl_number.text = str(check['number'])
            elif 'num' in check:
                self.lbl_number.text = str(check['num'])
            else:
                self.lbl_number.text = 'N/A'

            if 'amount' in check:
                self.lbl_amount.text = format_currency(check.amount, 'MXN', locale='es_mx')
            else:
                self.lbl_amount.text = None
            if 'bank' in check and self.bank is None:
                self.bank = check['bank']
            if 'account' in check and self.account is None:
                self.account = check['account']
        else:
            self.lbl_number.text = ''

    @property
    def bank(self):
        return self._bank

    @bank.setter
    def bank(self, x):
        self._bank = x
        bank = self._bank
        if bank is not None:
            if 'name' in bank:
                self.lbl_bank.setText(bank['name'])
            elif 'id' in bank:
                self.lbl_bank.setText(bank['id'])
            else:
                self.lbl_bank.setText('')
            for k in list(bank.keys()):
                if k not in ['id']:
                    del bank[k]
        else:
            self.lbl_bank.setText('')

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, x):
        self._account = x
        account = self._account
        if account is not None:
            if 'num' in account:
                self.lbl_account.setText(account['num'])
            elif 'number' in account:
                self.lbl_account.setText(account['number'])
            else:
                self.lbl_account.setText('')
            if 'bank' in account and self.bank is None:
                self.bank = account['bank']

            for k in list(account.keys()):
                if k not in ['number', 'num']:
                    del account[k]
        else:
            self.lbl_account.setText('')


class Charge_Check(Main_Window):
    def __init__(self, parent=None):
        Main_Window.__init__(self, parent)


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Charger()
    vv.check = dict({'number': 571, 'account': {'number': '0418574306'}, 'bank': {'id': 'MEX-072', 'name': 'Banorte'},
                'amount': Decimal('3638.28')})
    vv.show()
    sys.exit(app.exec_())
