from PySide.QtGui import QWidget, QVBoxLayout
from isis.data_model.table import Table
from decimal import Decimal
from isis.table_view import Table_View
from isis.utils import format_currency


class Model_Items(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        column = self.columns.add('last_price', Decimal)
        column.getter_data = lambda x: format_currency(x['price']['value'])
        self.columns.add('benefit', Decimal)
        self.readonly = True



class Widget_Items_Related(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.tableview = Table_View(self)
        self.model = Model_Items()
        layout_main = QVBoxLayout(self)
        self.setLayout(layout_main)
        layout_main.addWidget(self.tableview)

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price):
        self._price = price
        if price is not None:
            import pymysql
            d6 = pymysql.connect(host='comercialpicazo.com', port=3305, user='alejandro', password='5175202')
            d6_cursor = d6.cursor()
            d6_cursor.execute('select item.sku, item.description, key_price.`key`, last_price.value from perla.key_price left join itzamara.item on item.sku = perla.product_sku left join perla.last_purchase_price as last_price on last_price.sku = item.sku where key_price.price_id = %s;',
                              (price['id'], ))
            items = list()
            for sku, description, key, price_value in d6_cursor:
                item = {'sku': sku, 'description': description, 'price': {'value': price_value,
                                                                          'wholesale': False if key is None else True}}
                items.append(item)
            self.model.datasource = items



        else:
            self.model.datasource = None