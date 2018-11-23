from PySide.QtCore import *
from PySide.QtGui import *
from isis.kristine.accounts import Widget_Accounts
from isis.kristine.splits import Widget_Splits


class Accounting(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle(self.__class__.__name__)
        self.resize(800, 500)
        self.tabwidget = QTabWidget(self)
        self.setCentralWidget(self.tabwidget)
        self.tabaccounts = Widget_Accounts(self.tabwidget)
        self.tabwidget.addTab(self.tabaccounts, 'Accounts')
        self.tabaccounts.open_account.suscribe(self.handle_open_account)

    def handle_open_account(self, account):
        from pprint import pprint
        pprint(account)


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Accounting()
    vv.show()
    sys.exit(app.exec_())
