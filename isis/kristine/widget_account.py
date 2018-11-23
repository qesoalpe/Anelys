from isis.widget import Widget
from isis.label import Label
from PySide.QtGui import QGroupBox


class Widget_Account(QGroupBox):
    def __init__(self, *args, **kwargs):
        QGroupBox.__init__(self, *args, **kwargs)
        lbl_id = Label('id: ', self)
        lbl_type = Label('type: ', self)
        lbl_name = Label('name: ', self)
        lbl_fullpath = Label('fullpath: ', self)

        lbl_id.fix_size_based_on_font()
        lbl_type.fix_size_based_on_font()
        lbl_name.fix_size_based_on_font()
        lbl_fullpath.fix_size_based_on_font()

        self.lbl_id = Label(self)
        self.lbl_type = Label(self)
        self.lbl_name = Label(self)
        self.lbl_fullpath = Label(self)
        from PySide.QtGui import QGridLayout
        layout_main = QGridLayout(self)
        layout_main.addWidget(lbl_id, 0, 0)
        layout_main.addWidget(self.lbl_id, 0, 1)
        layout_main.addWidget(lbl_type, 0, 2)
        layout_main.addWidget(self.lbl_type, 0, 3)
        layout_main.addWidget(lbl_name, 1, 0)
        layout_main.addWidget(self.lbl_name, 1, 1, 1, -1)
        layout_main.addWidget(lbl_fullpath, 2, 0)
        layout_main.addWidget(self.lbl_fullpath, 2, 1, 1, -1)
        self.setLayout(layout_main)

        self._account = None

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, account):
        self._account = account
        if account is not None:
            self.lbl_id.text = account.id if 'id' in account else None
            self.lbl_type.text = account.account_type if 'account_type' in account else None
            self.lbl_name.text = account.name if 'name' in account else None
            self.lbl_fullpath.text = account.fullpath if 'fullpath' in account else None
        else:
            self.lbl_id.text = None
            self.lbl_type.text = None
            self.lbl_name.text = None
            self.lbl_fullpath.text = None
