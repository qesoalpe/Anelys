from isis.main_window import Main_Window
from isis.data_model.table import Table


class Debts_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('type', str)
        self.columns.add('folio', str)
        self.columns.add('datetime', str)
        self.columns.add('expires', str)
        self.columns.add('amount', str)
        self.columns.add('balance', str)


class Debts(Main_Window):
    def __init_(self):
        Main_Window.__init__(self)


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Debts()
    vv.show()
    sys.exit(app.exec_())
