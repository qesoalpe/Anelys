from sarah.acp_bson import Client
agent = Client('itzamara', 'itzamara')
# def get_items_related_factor(item_or_items):
#     msg_ask = {'type_message': 'request',
#                'request_type': 'get',
#                'get': 'itzamara/items_factor_related'}
#     if isinstance(item_or_items, dict):
#         msg_ask.item = item_or_items
#     else:
#         msg_ask['items'] = item_or_items
#
#     answer = agent_itzamara(msg_ask)
#     if isinstance(item_or_items, dict):
#         return answer.item
#     else:
#         return answer['items']


def get_items_factor_related(x):
    def get_item_items_factor_related(item):
        answer = agent({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
                        'item': item})
        if 'item' in answer and answer['item'] is not None:
            return answer['item']
        else:
            return item

    def get_items_items_factor_related(items):
        answer = agent({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
                        'items': items})
        if 'items' in answer and answer['items'] is not None:
            return answer['items']
        else:
            return items

    if isinstance(x, dict):
        if 'type' not in x or x['type'] == 'itzamara/item':
            return get_item_items_factor_related(x)
        elif 'type' in x and x['type'] == 'itzamara/item_list' and 'items' in x:
            return get_items_items_factor_related(x['items'])
    elif isinstance(x, list):
        return get_items_items_factor_related(x)

    return x


def find_one_item(query=None, sku=None):
    if query is None and sku is not None:
        query = {'sku': sku}
    answer = agent({'type_message': 'find_one', 'type': 'itzamara/item', 'query': query})
    if 'result' in answer:
        return answer['result']


def get_item_mass(item):
    msg = {'type_message': 'request', 'request_type': 'get',
           'get': 'itzamara/get_item_mass', 'item': item}
    answer = agent(msg)
    return answer.mass if 'mass' in answer else None


def item_has_expiration(item):
    msg = {'type_message': 'question', 'question': 'itzamara/item_expires', 'item': item}
    answer = agent(msg)
    return answer.answer
