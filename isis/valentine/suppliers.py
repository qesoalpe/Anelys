from katherine import d1
from isis.main_window import Main_Window
from isis.widget import Widget
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.v_box_layout import V_Box_Layout


class Suppliers_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('type', str)
        self.columns.add('name', str)
        self.columns['type'].getter_data = 'supplier_type'
        self.datasource = list()
        self.readonly = True


class Suppliers_Table_View(Table_View):
    pass


class Suppliers(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Suppliers')
        self.resize(700, 600)
        self.cwidget = Widget()
        self.table = Suppliers_Table_View(self.cwidget)

        layout_main = V_Box_Layout(self.cwidget)
        layout_main.addWidget(self.table)
        self.cwidget.layout = layout_main
        self.model = Suppliers_Model()
        self.table.model = self.model
        self.model.datasource = list(d1.valentine.supplier.find(projection={'_id': False}, sort=[('name', 1)]))


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Suppliers()
    mw.show()
    sys.exit(app.exec_())
