from sarah.acp_bson import Client
from dict import Dict as dict


agent = Client('', 'perla')


def find_perla_price(query=None, item=None, sku=None):
    msg = dict({'type_message': 'find', 'type': 'perla/price'})
    if query is not None:
        msg.query = query
    elif item is not None:
        msg.query = {'item': item}
    elif sku is not None:
        msg.query = {'sku': item}

    answer = agent(msg)
    if 'result' in answer:
        return answer.result
    else:
        return None
