from sarah.acp_bson import Recipient, Client, Pool_Handler
from katherine import d1, d5, d6, pymysql
import re
from dict import Dict as dict, List as list
from itzamara import key_to_sort_item


db_piper = d1.piper

coll_provider = db_piper.get_collection('provider')
agent_reina = Client('/piper', '/reina')
agent_perla = Client('/piper', 'perla')


def handle_action_piper_create_provider(msg):
    mprovider = msg['provider']
    msg_ask = {'type_message': 'find_one', 'type': mprovider['type'], 'query': mprovider}
    mprovider = agent_reina.send_msg(msg_ask)['result']
    provider = dict()
    provider['id'] = mprovider['id']
    if 'business_name' in mprovider:
        provider['business_name'] = mprovider['business_name']
    if 'name' in mprovider:
        provider['name'] = mprovider['name']
    provider['type'] = 'piper/provider'
    if 'type' in mprovider:
        provider['provider_type'] = mprovider['type']
    if 'rfc' in mprovider:
        provider['rfc'] = mprovider['rfc']
    coll_provider.insert(provider)
    del provider['_id']
    return {'provider': provider}


def handle_action_piper_creat_provider_not_sells(msg):
    session = d5.session()
    session.run('MATCH (provider{id:{provider_id}}), (item{sku:{item_sku}}) CREATE UNIQUE '
                '(provider)-[:not_sells]->(item);',
                {'provider_id': msg['provider']['id'], 'item_sku': msg['item']['sku']})
    session.close()


def handle_action_piper_remove_provider_not_sells(msg):
    provider_id = msg['provider']['id']
    item_sku = msg['item']['sku']
    session = d5.session()
    session.run('MATCH (provider{id:{provider_id}})-[rel:NOT_SELLS|not_sells]->(item{sku:{item_sku}}) DELETE rel;',
                {'provider_id': provider_id, 'item_sku': item_sku})
    session.close()


def handle_get_piper_provider_not_sells(msg):
    session = d5.session()
    provider_id = msg['provider']['id']
    result = session.run('MATCH (provider{id:{id}})-[:NOT_SELLS|not_sells]->(item) RETURN item.sku as sku, '
                         'item.description as description, item.type as type;', {'id': provider_id})
    items = list()
    for record in result:
        item = dict()
        if record['sku'] is not None:
            item['sku'] = record['sku']
        if record['description'] is not None:
            item['description'] = record['description']
        if record['type'] is not None:
            item['type'] = record['type']
        if len(item) == 1 and 'sku' in item:
            items.append(item['sku'])
        elif len(item):
            items.append(item)
    session.close()
    return {'result': items}


def handle_get_piper_provider_sells(msg):
    d5_session = d5.session()
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    provider = msg['provider']
    d6_cursor.execute('SELECT DISTINCT item.sku, item.description FROM itzamara.item inner join perla.purchase_price '
                      'ON purchase_price.local_item_sku = item.sku WHERE provider_id = %s AND purchase_price.type = 23',
                      (provider['id'],))
    result = list(d6_cursor)
    result.skus = list()
    rr = d5_session.run('MATCH (provider{id: {provider_id}})-[:sells]->(item) RETURN item.sku as sku, '
                        'item.description as description;', {'provider_id': provider.id})
    for d5_record in rr:
        item = dict()
        if d5_record['sku'] is not None:
            item['sku'] = d5_record['sku']
        if d5_record['description'] is not None:
            item['description'] = d5_record['description']
        if 'sku' in item:
            if item.sku not in result.skus:
                result.skus.append(item.sku)
                result.append(item)

    d5_session.close()
    d6_cursor.close()

    msg = {'type_message': 'request', 'request_type': 'get', 'get': 'perla/provider_sells', 'provider': provider}
    answer = agent_perla.send_msg(msg)
    for item in answer.result:
        if item.sku not in result.skus:
            result.skus.append(item.sku)
            result.append(item)
    del result.skus
    result.sort(key=key_to_sort_item)
    return {'result': result}


def handle_find_piper_item(msg):
    query = msg.query
    provider_id = query.provider.id
    if 'descritpion' in query:
        description = '%' + query.description.replace(' ', '%') + '%'
    elif 'item' in query and 'description' in query.item:
        description = '%' + query.item.description.replace(' ', '%') + '%'
    else:
        description = '%'
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    d6_cursor.execute('select sku, description, price from piper.item where provider_id = %s and description like %s;',
                      (provider_id, description))
    result = list(d6_cursor)
    d6.close()
    result.sort(key=key_to_sort_item)
    return {'result': result}


def handle_find_piper_item_document(msg):
    query = msg.query
    provider_id = query.provider.id
    if 'document_type' in query:
        document_type = query['document_type']
    else:
        document_type = 'NULL'
    if 'description' in query:
        description = '%' + query['description'].replace('', '%') + '%'
    elif 'item' in query and 'description' in query['item']:
        description = '%' + query['item']['description'].replace('', '%') + '%'
    else:
        description = '%'

    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    r = d6_cursor.execute('select sku, description, price from piper.item_document WHERE provider_id = %s and '
                          'document_type = %s and description like %s;',
                          (provider_id, document_type, description))
    result = list(d6_cursor)
    return {'result': result}


def handle_find_piper_provider(msg):
    l_filter = dict()
    for key, value in msg['query'].items():
        if key == 'name':
            if isinstance(value, dict):
                for k2, v2 in value.items():
                    if k2 == '!like':
                        l_filter['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.IGNORECASE)
    result = list(coll_provider.find(l_filter, {'_id': False}))
    return {'result': result}


def handle_find_one_piper_item_document(msg):
    query = msg['query']
    provider_id = query['provider']['id']
    if 'document_type' in query:
        document_type = query['document_type']
    elif 'document_type' in msg:
        document_type = msg['document_type']
    else:
        document_type = '%'

    if 'sku' in query:
        sku = query['sku']
    elif 'item' in query and 'sku' in query['item']:
        sku = query['item']['sku']
    else:
        sku = 'alskd'

    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    d6_cursor.execute('select sku, description, price from piper.item_document where provider_id = %s and '
                      'document_type = %s and sku = %s limit 1', (provider_id, document_type, sku))
    if d6_cursor.rowcount == 1:
        result = d6_cursor.fetchone()
    else:
        result = None
    d6_cursor.close()
    return {'result': result}


def handle_find_one_piper_provider(msg):
    l_filter = dict()
    for key, value in msg['query'].items():
        if key == 'id':
            l_filter['id'] = value
        elif key == 'rfc':
            l_filter['rfc'] = value
    result = coll_provider.find_one(l_filter, {'_id': False})
    return {'result': result}


rr = Pool_Handler()
rr.reg('type_message=action.action=piper/create_provider', handle_action_piper_create_provider)
rr.reg('type_message=action.action=piper/create_provider_not_sells', handle_action_piper_creat_provider_not_sells)
rr.reg('type_message=action.action=piper/remove_provider_not_sells', handle_action_piper_remove_provider_not_sells)
rr.reg('type_message=request.request_type=get.get=piper/provider_not_sells', handle_get_piper_provider_not_sells)
rr.reg('type_message=request.request_type=get.get=piper/provider_sells', handle_get_piper_provider_sells)
rr.reg('type_message=find.type=piper/item', handle_find_piper_item)
rr.reg('type_message=find.type=piper/item_document', handle_find_piper_item_document)
rr.reg('type_message=find.type=piper/provider', handle_find_piper_provider)
rr.reg('type_message=find_one.type=piper/item_document', handle_find_one_piper_item_document)
rr.reg('type_message=find_one.type=piper/provider', handle_find_one_piper_provider)


if __name__ == '__main__':
    print("I'm piper")
    recipient = Recipient()
    recipient.prepare('/piper', rr)
    recipient.begin_receive_forever()


