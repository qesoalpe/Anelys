from isis.dialog import Dialog
from isis.label import Label
from isis.radio_group import Radio_Group
from isis.decimal_edit import Decimal_Edit
from isis.widget import Widget

class Widget_Map_Price(Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)


class Map_Price(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, *kwargs)
        self.lbl_id =


class Products_Price(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        self.lbl_sku = Label(self)
        self.lbl_description = Label(self)
        self._product = None
        self.rg_map_price = Radio_Group(self)
        self.rg_map_price.items.add('Ninguno', None)
        self.rg_map_price.items.add('Propio', 'own')
        self.rg_map_price.items.add('perla/map_price', 'perla/map_price')


    @property
    def product(self):
        return self._product

    @product.setter
    def product(self, product):
        self._product = product
