# class Daemon(object):
#     def __init__(self):
#         self.name = None
#         self.id = None
#         self.handler = Pool_Handler()
#
#     def __setattr__(self, key, value):
#         self.handler[key] = value
from dict import Dict, Dict as dict
from sarah.acp_bson import Client
from katherine import citlali_maria_config, pymysql
from decimal import Decimal as D


agent_backend = Client('', 'portia/backend')


def handle_action_portia_print_document(msg):
    citlali_maria = pymysql.connect(**citlali_maria_config)
    citla_cursor = citlali_maria.cursor()
    document = msg.document
    _msg = Dict({'type_message': 'action', 'action': 'portia/print_document'})
    if 'params' not in msg:
        params = Dict()
        _msg.params = params
    else:
        params = msg.params
        _msg.params = params
    if 'printer' not in params:
        r = citla_cursor.execute('select printer from portia.document_type_printer where document_type = %s limit 1;',
                                 (document.type,))
        if r == 1:
            params.printer, = citla_cursor.fetchone()

    if document.type == 'serena/ticket':
        for item in document['items']:
            if 'price' in item:
                price = item.price
                if not isinstance(price, (D, int, float)) and isinstance(price, dict) and 'value' in price:
                    item.price = price.value
            if 'amount' not in item and 'quanty' in item and 'price' in item:
                item.amount = item.quanty * item.price
        if 'client' in document:
            client = document.client
            if isinstance(client, dict) and 'name' in client:
                document.client = client.name

        _msg.document = document
        if 'copy' not in params:
            params.copy = False

    if 'document' in _msg:
        agent_backend(_msg)

    citla_cursor.close()
    citlali_maria.close()


def handle_action_portia_print_prices(msg):
    items = msg['items']



if __name__ == '__main__':
    from sarah.handler import Pool_Handler
    from sarah.acp_bson import Recipient
    h = Pool_Handler()
    h['type_message=action.action=portia/print_document'] = handle_action_portia_print_document
    h['type_message=action.action=portia/print_prices'] = handle_action_portia_print_prices
    recipient = Recipient()
    recipient.prepare('portia', h)
    recipient.begin_receive_forever()
