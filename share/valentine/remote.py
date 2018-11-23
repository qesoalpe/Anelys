from dict import Dict, Dict as dict
from sarah.acp_bson import Client
agent_valentine = Client('', 'valentine')


def make_movement(items=None, storage=None, origen=None, type=None, from_=None, to=None):
    msg = Dict({'type_message': 'action', 'action': 'valentine/make_movement', 'items': items, 'origen': origen})
    if type is not None:
        msg.mov_type = type

    if from_ is  None or to is None and storage is not None:
        msg.storage = storage
    elif from_ is not None and to is not None:
        msg['from'] = from_
        msg.to = to
    return agent_valentine(msg)


def get_inventory_absolut(item_or_items, storage=None):
    msg = dict({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut'})
    if storage is not None:
        msg.storage = storage
    if isinstance(item_or_items, list):
        msg['items'] = item_or_items
    else:
        msg.item = item_or_items
    a = agent_valentine(msg)

    if isinstance(item_or_items, list):
        return a['items']
    else:
        return a.item


def find_one_storage(query):
    if isinstance(query, str):
        query = dict({'id': query})
    msg = dict({'type_message': 'find_one', 'type': 'valentine/storage', 'query': query})
    answer = agent_valentine(msg)
    if 'result' in answer:
        return answer.result
