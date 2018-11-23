from isis.event import Event
from isis.tree_view import Tree_View
from isis.data_model.tree import Tree
from decimal import Decimal
from isis.widget import Widget
from dict import Dict
from PySide.QtGui import QVBoxLayout
from isis.main_window import Main_Window


class Model_Accounts(Tree):
    def __init__(self):
        Tree.__init__(self)
        self.columns.add('name', str)
        self.columns.add('id', str)
        self.columns.add('description', str)
        self.columns.add('balance', Decimal, 'c')

        def f(x):
            if 'balance' in x:
                if 'nature' in x:
                    if x.nature == 'debitable':
                        return x.balance
                    elif x.nature == 'creditable':
                        return -x.balance
                    else:
                        return x.balance
                else:
                    return x.balance

        self.columns['balance'].getter_data = f


class Widget_Accounts(Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.resize(500, 500)
        self.setWindowTitle('Accounts')
        self.treeview = Tree_View(self)

        self.model = Model_Accounts()
        self.treeview.model = self.model

        layout_main = QVBoxLayout(self)
        layout_main.addWidget(self.treeview)

        self.layout = layout_main

        from pymongo import MongoClient
        d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
        d1.admin.authenticate('alejandro', '47exI4')

        def populate_children(account):
            children = list()
            for child in d1.kristine.account.find({'parent.id': account.id}, {'_id': False}):
                child.parent = account
                children.append(child)
            if len(children):
                for child in children:
                    populate_children(child)
                account.children = children

        def put_balance(account):
            balance = Decimal()
            from katherine import d6_config
            if 'children' in account:
                for child in account.children:
                    put_balance(child)
                    balance += child.balance
            import pymysql
            d6 = pymysql.connect(**d6_config)
            d6_cursor = d6.cursor()
            d6_cursor.execute('select ifnull(sum(value), 0) from kristine.split where account_id = %s;', (account.id, ))
            b, = d6_cursor.fetchone()
            if b is not None:
                balance += b

            account.balance = balance

        root = Dict({'id': 'root'})
        populate_children(root)
        put_balance(root)
        # root.children.append(Dict({'name': 'Splits without Transaction'}))

        self.model.rootitem = root
        self.treeview.expandAll()
        self.treeview.resizeColumnsToContents()
        self.open_account = Event()

        def h(x):
            _account = x.internalPointer().data
            account = Dict()
            for k in ['id', 'name', 'type', 'nature', 'type', 'class']:
                if k in _account:
                    account[k] = _account[k]
            from isis.kristine.splits import Splits
            vv = Splits()
            vv.account = account
            vv.show()

        self.treeview.double_clicked.suscribe(h)


class Main_Window_Accounts(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Accounts')
        self.resize(700, 600)
        self.cwidget = Widget_Accounts(self)
        self.setCentralWidget(self.cwidget)

        toolbar = self.addToolBar('file')
        create_transaction = toolbar.addAction('create_transaction')
        create_transaction.triggered.connect(self.handle_create_transaction_triggered)

    def handle_create_transaction_triggered(self):
        from isis.kristine.create_transaction import Create_Transaction
        vv = Create_Transaction(self)
        vv.show()


if __name__ == '__main__':
    from PySide.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    vv = Main_Window_Accounts()
    vv.show()
    sys.exit(app.exec_())
