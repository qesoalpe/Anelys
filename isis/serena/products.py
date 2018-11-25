from isis.main_window import Main_Window
from isis.data_model.table import Table
from decimal import Decimal as D
from isis.table_view import Table_View
from isis.widget import Widget
from isis.v_box_layout import V_Box_Layout
from itzamara import key_to_sort_item
from dict import Dict as dict, List as list
from katherine import d1


class Productos_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('price', D, 'c')
        self.columns['price'].getter_data = self.getter_data_price

    @staticmethod
    def getter_data_price(row):
        if 'price' in row:
            price = row.price
            if isinstance(price, D):
                return price
            elif isinstance(price, dict) and 'value' in price:
                return price.value


class Products_TV(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectRows)


class Products(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Productos')
        self.resize(1200, 800)
        self.cwidget = Widget(self)
        self.table = Products_TV(self.cwidget)
        self.productsmodel = Productos_Model()
        self.table.model = self.productsmodel

        products = list(d1.serena.product.find({}, {'_id': False}))
        products.sort(key=key_to_sort_item)
        self.productsmodel.datasource = products
        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addWidget(self.table)
        self.cwidget.layout = layoutmain


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Products()
    mw.show()
    sys.exit(app.exec_())
