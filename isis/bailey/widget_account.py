from isis.grid_layout import Grid_Layout
from isis.label import Label
from isis.group_box import Group_Box
from isis.push_button import Push_Button
from isis.event import Event
from PySide2.QtCore import Qt
from isis.bailey.search_account import Search_Account


class Widget_Account(Group_Box):
    def __init__(self, *args, **kwargs):
        Group_Box.__init__(self, *args, **kwargs)
        lbl_id = Label('id: ', self)
        lbl_number = Label('number: ', self)
        lbl_clabe = Label('clabe: ', )
        lbl_bank = Label('bank: ', self)
        lbl_titular = Label('titular: ', self)
        lbl_id.fix_size_based_on_font()
        lbl_number.fix_size_based_on_font()
        lbl_clabe.fix_size_based_on_font()
        lbl_bank.fix_size_based_on_font()
        lbl_titular.fix_size_based_on_font()

        self.lbl_id = Label(self)
        self.lbl_number = Label(self)
        self.lbl_clabe = Label(self)
        self.lbl_bank = Label(self)
        self.lbl_titular = Label(self)

        layout_main = Grid_Layout(self)
        layout_main.addWidget(lbl_id, 1, 0)
        layout_main.addWidget(self.lbl_id, 1, 1)
        layout_main.addWidget(lbl_number, 2, 0)
        layout_main.addWidget(self.lbl_number, 2, 1)
        layout_main.addWidget(lbl_clabe, 3, 0)
        layout_main.addWidget(self.lbl_clabe, 3, 1, 1, -1)
        layout_main.addWidget(lbl_titular, 3, 2)
        layout_main.addWidget(self.lbl_titular, 3, 3, 1, -1)
        layout_main.addWidget(lbl_bank, 2, 2)
        layout_main.addWidget(self.lbl_bank, 2, 3, 1, -1)

        self.account_changed = Event()

        self.setLayout(layout_main)
        self._account = None
        self.btn_change = None
        self._label = None

    @property
    def label(self):
        if self._label is not None:
            return self._lable.text

    @label.setter
    def label(self, label):
        if label is not None:
            if self._label is None:
                self._label = Label(label, self)
                layout = self.layout()
                layout.addWidget(self._label, 0, 0)
            elif self._label is not None:
                self._label.text = label
            self._label.fix_size_based_on_font()
        elif self._label is None:
            layout = self.layout()
            layout.removeWidget(self._label)
            del self._label

    @property
    def with_change_button(self):
        return self.btn_change is not None

    @with_change_button.setter
    def with_change_button(self, value):
        assert isinstance(value, bool)
        if value != self.with_change_button:
            layout = self.layout()
            if value:
                self.btn_change = Push_Button('change', self)
                layout.addWidget(self.btn_change, 0, 3, Qt.AlignRight)
                def h():
                    searcher = Search_Account(self)
                    searcher.exec_()
                    if searcher.selected is not None:
                        self.account = searcher.selected

                self.btn_change.clicked.connect(h)
            else:

                layout.removeWidget(self.btn_change)
                del self.btn_change

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, account):
        self._account = account
        if account is not None:
            self.lbl_id.text = account.id if 'id' in account else None
            self.lbl_number.text = account.number if 'number' in account else None
            self.lbl_clabe.text = account.clabe if 'clabe' in account else None
            self.lbl_bank.text = account.bank.name if 'bank' in account and 'name' in account.bank else None
            self.lbl_titular.text = account.titular.name if 'titular' in account and 'name' in account.titular else None
        else:
            self.lbl_id.text = None
            self.lbl_number.text = None
            self.lbl_clabe.text = None
            self.lbl_bank.text = None
            self.lbl_titular.text = None
        self.account_changed(account)