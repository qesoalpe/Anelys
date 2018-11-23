from isis.data_model.table import Table
from decimal import Decimal
from sarah.acp_bson import Client
from isis.dialog_search_text import Dialog_Search_Text
from dict import Dict, Dict as dict


class Search_Product(Dialog_Search_Text):
    def __init__(self, *args, **kwargs):
        Dialog_Search_Text.__init__(self, *args, **kwargs)
        self.resize(550, 550)
        self.setWindowTitle('Search_Product')
        self.agent = Client('Search_Product', 'serena')
        self.agent_itzamara = Client('Search_Product', 'itzamara')
        self.store = None
        self.search_by_sku = True
        self.search_by_code_ref = True
        self._agent_valentine = None
        self.item_selected.suscribe(self.handle_item_selected)

    @staticmethod
    def handle_item_selected(item):
        for k in list(item.keys()):
            if k not in ['sku', 'type', 'name', 'mass', 'description']:
                del item[k]

    @property
    def agent_valentine(self):
        if self._agent_valentine is None:
            self._agent_valentine = Client('', 'valentine')
        return self._agent_valentine

    def searching(self, e):
        if self.search_by_sku:
            msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': e['text']}}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer['result'] is not None:
                result = answer.result
                if 'type' in result and result.type != 'serena/product':
                    result.product_type = result.type
                    result.type = 'serena/product'
                elif 'type' not in result:
                    result.type = 'serena/product'
                e.selected = result
                return

        if self.search_by_code_ref:
            msg = {'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/item_related_to_code_ref',
                   'code_ref': e.text}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer.result is not None:
                result = answer.result
                if 'type' in result and result.type != 'serena/product':
                    result.product_type = result.type
                    result.type = 'serena/product'
                elif 'type' not in result:
                    result.type = 'serena/product'
                e.selected = result
                return

        msg = Dict({'type_message': 'find', 'type': 'serena/product', 'query': {'description': {'!like': e.text}},
                    'limit': 50, 'sort': True})
        if self.store is not None:
            msg.query.store = self.store
        answer = self.agent.send_msg(msg)
        items = answer.result

        if len(items) > 1:
            msg = dict({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut',
                        'items': answer.result})
            if self.store is not None:
                msg.store = self.store
            answer = self.agent_valentine.send_msg(msg)
            if 'items' in answer:
                items = answer['items']

        table = Table('products')
        table.columns.add('sku', str)
        table.columns.add('description', str)
        table.columns.add('price', Decimal, 'c')
        table.columns.add('inventory', Decimal, '#,##0.###')

        def getter_price(row):
            if 'price' in row:
                price = row.price
                if isinstance(price, (int, Decimal)):
                    return price
                elif isinstance(price, Dict) and 'value' in price:
                    return price.value

        table.columns['price'].getter_data = getter_price
        table.columns['inventory'].getter_data = ['inventory_absolut', 'inventory']
        e.table = table
        e.list = items
        table.datasource = e.list


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    vv = Search_Product()
    vv.store = {'id': '42-3'}
    vv.exec_()
    from pprint import pprint
    pprint(vv.selected)
