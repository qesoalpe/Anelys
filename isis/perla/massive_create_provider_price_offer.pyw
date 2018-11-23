from isis.itzamara.search_item import Search_Item
from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
from isis.widget import Widget
from isis.main_window import Main_Window
from isis.table_view import Table_View
from isis.data_model.table import Table
from decimal import Decimal as D
from dict import Dict as dict, List as list
from isis.v_box_layout import V_Box_Layout
from itzamara.remote import find_one_item
from isis.message_box import Message_Box


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('price', D, 'c')
        self.columns.add('description', str)
        self.datasource = list()
        self.with_new_empty_row = True
        self.columns['sku'].changing_item_value = self.changing_item_value_sku
        self.columns['description'].changing_item_value = self.changing_item_value_description

    def changing_item_value_sku(self, item, value):
        if value is not None and value:
            if 'sku' in item and item.sku == value:
                return False
            result = find_one_item(sku=value)
            if result is not None:
                self.set_item(item, result)
            else:
                self.clear_item(item)
        elif 'sku' in item:
            self.clear_item(item)
        else:
            return False

    def changing_item_value_description(self, item, value):
        if value is not None and value:
            if 'description' in item and item.description == value:
                return False
            searcher = Search_Item()
            result = searcher.search(value)
            if result is not None:
                self.set_item(item, result)
            else:
                self.clear_item(item)
        elif 'description' in item:
            self.clear_item(item)
        else:
            return False

    @staticmethod
    def set_item(item, new_item):
        if 'sku' in new_item:
            item.sku = new_item.sku
        elif 'sku' in item:
            del item.sku

        if 'description' in new_item:
            item.description = new_item.description
        elif 'description' in item:
            del item.description

        if 'type' in new_item:
            item.type = new_item.type
        elif 'item' in item:
            del item.type

    @staticmethod
    def clear_item(item):
        if 'sku' in item:
            del item.sku
        if 'description' in item:
            del item.description
        if 'type' in item:
            del item.type


class Items_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.enable_delete_row_with_supr = True


class Massive_Create_Provider_Price_Offer(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(700, 500)
        self.setWindowTitle('Crear precios ofrecidos por el proveedor masivamente')
        cwidget = Widget()
        self.central_widget = cwidget
        self.widget_provider = Widget_Viewer_Provider(cwidget)
        self.widget_provider.with_button_change = True
        self.tableview = Items_Table_View(cwidget)

        self.itemsmodel = Items_Model()
        self.tableview.model = self.itemsmodel

        layoutmain = V_Box_Layout(cwidget)
        layoutmain.addWidget(self.widget_provider)
        layoutmain.addWidget(self.tableview)
        cwidget.layout = layoutmain
        tool_bar = self.addToolBar('File')
        action_create = tool_bar.addAction('Create')
        action_create.triggered.connect(self.create)

    def create(self):
        if self.widget_provider.provider is None:
            Message_Box.warning(self, 'error', 'Debe de contener un proveedor')
            return
        provider = self.widget_provider.provider
        items = list([item for item in self.itemsmodel.datasource if 'sku' in item])
        for item in items:
            if 'price' not in item:
                Message_Box.warning(self, 'error', 'todos los artiulos deben de contener precio')
                return
        from sarah.acp_bson import Client
        agent_perla = Client('', 'perla')
        msg = dict({'type_message': 'action', 'action': 'perla/create_provider_price_offer', 'provider': provider})
        for item in items:
            msg.item = {'sku': item.sku, 'description': item.description}
            msg.price = item.price
            agent_perla(msg)
        Message_Box.information(self, 'Successfull', 'Se han registrado todos los articulos')
        self.widget_provider.provider = None
        self.itemsmodel.datasource = None


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    mw = Massive_Create_Provider_Price_Offer()
    mw.show()
    sys.exit(app.exec_())
