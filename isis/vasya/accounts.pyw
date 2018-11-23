from PySide.QtGui import *
from PySide.QtCore import Qt
from isis.data_model.table import Table
from decimal import Decimal
from isis.table_view import Table_View
from make_transaction import Make_Transaction


class Model_Accounts(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('name', str)
        self.columns.add('type', str)
        self.columns['type'].getter_data = lambda x: x['account_type'] if 'account_type' in x else x['type'] if 'type' in x else None
        self.columns.add('balance', Decimal, 'c')
        self.readonly = True


class Table_View_Accounts(Table_View):
    def __init__(self, parent):
        Table_View.__init__(self, parent)
        self.windowparent = None

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            action_make_tx = menu.addAction('make transaction')
            i = self.indexAt(event.pos())
            account = self.model.datasource[i.row()]

            def handler():
                vv = Make_Transaction(self.windowparent)
                vv.origen = account
                vv.show()
            action_make_tx.triggered.connect(handler)
            menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class Accounts(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Accounts')
        self.resize(700, 400)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        self.tableview = Table_View_Accounts(self.cwidget)
        self.windowparent = self
        layoutmain = QVBoxLayout()
        layoutmain.addWidget(self.tableview)

        self.cwidget.setLayout(layoutmain)

        self.model = Model_Accounts()

        self.tableview.model = self.model
        from sarah.acp_bson import Client

        agent_vasya = Client('vasya/accounts', 'vasya')
        answer = agent_vasya({'type_message': 'find', 'type': 'vasya/account', 'projection': {'balance': True}})
        if 'result' in answer and answer['result'] is not None:
            self.accounts = answer['result']
        else:
            self.accounts = None

        self.model.datasource = self.accounts


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Accounts()
    vv.show()
    sys.exit(app.exec_())
