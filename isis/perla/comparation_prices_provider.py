from katherine import d1
from dict import Dict as dict, List as list
from sarah.acp_bson import Client
from utils import find_one


agent_perla = Client('', 'perla')

providers = list()

for k in ['61-3', '61-10', '61-12', '3-3', '3-6', '204-11']:
    providers.append(d1.piper.provider.find_one({'id': k}, {'_id': False}))


items = d1.itzamara.item_list.find_one({'id': '157-25'}, {'_id': False, 'items': True})['items']

for item in items:
    item.prices = dict()
    answer = agent_perla({'type_message': 'find', 'type': 'perla/purchase_price', 'query': {'my_item': item}})
    prices = answer.result
    answer = agent_perla({'type_message': 'find', 'type': 'perla/provider_offer_price', 'query': {'my_item': item}})
    prices.extend(answer.result)
    prices.sort(key=lambda x: x.datetime, reverse=True)
    prices = list(filter(lambda x: 'id' in x.provider, prices))
    for provider in providers:
        price = find_one(lambda x: x.provider.id == provider.id, prices)
        if price is not None:
            item.prices[provider.id] = price


from isis.main_window import Main_Window
from isis.data_model.table import Table, Columns
from isis.table_view import Table_View
from isis.widget import Widget
from isis.v_box_layout import V_Box_Layout

from decimal import Decimal as D
from PySide2.QtCore import Qt


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self._providers = None
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns_prices = Columns(self)
        self.readonly = True
    @property
    def providers(self):
        return self._providers

    @providers.setter
    def providers(self, providers):
        self._providers = providers
        self.columns_prices._columns.clear()
        self.modelReset.emit()
        if providers is not None:
            for provider in providers:
                # self.columns_prices.add(provider.id + '//type', str)
                self.columns_prices.add(provider.id + '//datetime', str)
                self.columns_prices.add(provider.id + '//price', D, 'c')

    def columnCount(self, parent=None):
        return len(self.columns) + len(self.columns_prices)

    def data(self, index, role):
        if index.column() >= len(self.columns):
            if role == Qt.DisplayRole:
                item = self.datasource[index.row()]
                column = self.columns_prices[index.column() - len(self.columns)]
                i = index.column() - len(self.columns)
                provider = self.providers[i // 2]
                if provider.id in item.prices:
                    price = item.prices[provider.id]
                    field = i % 2
                    if field == 2:
                        return column.format_data_display(price.type)
                    elif field == 0:
                        return column.format_data_display(price.datetime)
                    elif field == 1:
                        return column.format_data_display(price.value)
        else:
            return Table.data(self, index, role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and section >= len(self.columns):
            if role == Qt.DisplayRole:
                section = section - len(self.columns)
                return self.columns_prices[section].fieldname
        else:
            return Table.headerData(self, section, orientation, role)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class Comparation_Prices_Provider(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(1200, 500)
        self.setWindowTitle('Tabla de Comparacion de Precios')
        self.cwidget = Widget(self)
        self.table = Table_View(self.cwidget)

        layout_main = V_Box_Layout(self.cwidget)
        layout_main.addWidget(self.table)
        self.cwidget.layout = layout_main

        self.items = Items_Model()
        self.items.providers = providers
        self.items.datasource = items

        self.table.model = self.items


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Comparation_Prices_Provider()
    mw.show()
    sys.exit(app.exec_())
