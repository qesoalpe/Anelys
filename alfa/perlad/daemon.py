from decimal import Decimal as D
from anelys import get_id_with_name
from datetime import datetime
from isodate import datetime_isoformat
from sarah import dictutils
from sarah.acp_bson import Client, Recipient, Pool_Handler
from copy import deepcopy
from dict import Dict as dict, List as list
from katherine import d1, d5, d6, pymysql


perla_db = d1.perla

coll_provider_price_offer = perla_db.get_collection('provider_price_offer')
coll_purchase_price = perla_db.get_collection('purchase_price')
coll_scale_prices = perla_db.get_collection('scale_prices')


emitter_stamp = {'id': '/perla'}
agent_itzamara = Client(emitter_stamp, '/itzamara')
agent_ella = Client(emitter_stamp, '/ella')
agent_piper = Client(emitter_stamp, 'piper')


def convert_purchase_price_mongo_to_maria(bethesda_purchase_price_mongo):
    mm = bethesda_purchase_price_mongo
    mapr = dict()
    if 'id' in mm:
        mapr['id'] = mm['id']
    else:
        mapr['id'] = None

    if 'type' in mm:
        if mm['type'] == 'perla/purchase_price':
            mapr['type'] = 23
        elif mm['type'] == 'perla/purchase_price/disaggregated':
            mapr['type'] = 33
        else:
            mapr['type'] = None
    else:
        mapr['type'] = None

    if 'datetime' in mm:
        mapr['datetime'] = mm['datetime']
    else:
        mapr['datetime'] = None

    if 'provider' in mm:
        provider = mm['provider']
        if 'id' in provider:
            mapr['provider_id'] = provider['id']
        else:
            mapr['provider_id'] = None
        if 'business_name' in provider:
            mapr['provider_name'] = provider['business_name']
        elif 'name' in provider:
            mapr['provider_name'] = provider['name']
    else:
        mapr['provider_id'] = None
        mapr['provider_name'] = None

    mapr['local_item_sku'] = mm['my_item']['sku']
    mapr['local_item_description'] = mm['my_item']['description']
    if 'provider_item' in mm:
        mapr['provider_item_sku'] = None
        mapr['provider_item_description'] = None
    elif 'provider_item' in mm['my_item']:
        provider_item = mm['my_item']['provider_item']
        if 'sku' in provider_item:
            mapr['provider_item_sku'] = provider_item['sku']
        else:
            mapr['provider_item_sku'] = None

        if 'description' in provider_item:
            mapr['provider_item_description'] = provider_item['description']
        else:
            mapr['provider_item_description'] = None
    else:
        mapr['provider_item_sku'] = None
        mapr['provider_item_description'] = None
    mapr['price_value'] = mm['value']
    if 'aggregate' in mm:
        aggregate = mm['aggregate']
        mapr['aggregate_local_sku'] = aggregate['my_item']['sku']
        # mapr['aggregate_local_description'] = aggregate['my_item']['description']
        mapr['aggregate_price_id'] = aggregate['price']['id']
    else:
        mapr['aggregate_local_sku'] = None
        mapr['aggregate_price_id'] = None
    if 'purchase' in mm and 'id' in mm['purchase']:
        mapr['purchase_id'] = mm['purchase']['id']
    else:
        mapr['purchase_id'] = None
    return mapr


def convert_purchase_price_maria_to_mongo(bethesda_purchase_price_mariadb):
    row = bethesda_purchase_price_mariadb
    if not isinstance(row, dict):
        row = dict(row)

    price = dict()
    price.id = row['id'] if isinstance(row['id'], str) else str(row['id'], 'utf8') if isinstance(row, (bytes, bytearray)) else None
    price.type = 'perla/purchase_price' if row['type'] == 23 else 'perla/purchase_price/disaggregated' if row.type == 33 else None
    price.datetime = datetime_isoformat(row.datetime)

    if row.provider_id is not None or row.provider_name is not None:
        provider = dict()
        if row.provider_id is not None:
            provider.id = row.provider_id if isinstance(row.provider_id, str) else str(row.provider_id, 'utf8') \
                if isinstance(row.provider_id, (bytes, bytearray)) else None

        if row['provider_name'] is not None:
            provider.name = row.provider_name
        price.provider = provider

    if row['provider_item_sku'] is not None or row['provider_item_description'] is not None:
        provider_item = dict()
        if row.provider_item_sku is not None:
            provider_item.sku = row.provider_item_sku
        if row.provider_item_description is not None:
            provider_item.description = row.provider_item_description
        price.provider_item = provider_item

    my_item = dict()
    if row['local_item_sku'] is not None:
        my_item['sku'] = row['local_item_sku']
    if row['local_item_description'] is not None:
        my_item['description'] = row['local_item_description']
    price['my_item'] = my_item
    price['value'] = row['price_value']
    if row['aggregate_price_id'] is not None or row['aggregate_local_sku'] is not None:
        aggregate = dict()
        if row['aggregate_price_id'] is not None:
            aggregate['price'] = dict()
            if isinstance(row['aggregate_price_id'], str):
                aggregate['price']['id'] = row['aggregate_price_id']
            elif isinstance(row['aggregate_price_id'], (bytes, bytearray)):
                aggregate['price']['id'] = str(row['aggregate_price_id'], 'utf8')
        if row['aggregate_local_sku'] is not None:
            aggregate['my_item'] = {'id': row['aggregate_local_sku']}
        price['aggregate'] = aggregate
    if row['purchase_id'] is not None:
        if isinstance(row['purchase_id'], (bytearray, bytes)):
            price['purchase'] = {'id': row['purchase_id'].decode()}
        else:
            price['purchase'] = {'id': row['purchase_id']}

    return price


def persist_bethesda_perla_purchase_price(purchase_price):
    d6.ping(True)
    d6_cursor = d6.cursor()
    if 'value' not in purchase_price or purchase_price['value'] == D():
        return

    mari_price = convert_purchase_price_mongo_to_maria(purchase_price)
    d6_cursor.execute('INSERT perla.purchase_price (id, type, purchase_id, provider_id, provider_name, provider_item_sku, '
                      'provider_item_description, local_item_sku, local_item_description, price_value, datetime, '
                      'aggregate_price_id, aggregate_local_sku) VALUES (%(id)s, %(type)s, %(purchase_id)s, '
                      '%(provider_id)s, %(provider_name)s, %(provider_item_sku)s, %(provider_item_description)s, '
                      '%(local_item_sku)s, %(local_item_description)s, %(price_value)s, %(datetime)s, '
                      '%(aggregate_price_id)s, %(aggregate_local_sku)s);', mari_price)
    d6_cursor.close()
    dictutils.dec_to_float(purchase_price)
    coll_purchase_price.insert(purchase_price)
    del purchase_price['_id']
    dictutils.float_to_dec(purchase_price)


def update_perla_price_value(price, product, datetime):
    d6.ping(True)
    d6_cursor = d6.cursor()
    if product is not None:
        param = {'product_sku': product['sku'], 'product_description': product['description'], 'datetime': datetime,
                 'price_value': price['value']}
        if 'wholesale' in price:
            param['price_wholesale'] = price['wholesale']
        else:
            param['price_wholesale'] = None

        d6_cursor.execute('INSERT perla.price_history (product_sku, product_description, price_wholesale, datetime, '
                          'price_value) VALUES (%(product_sku)s, %(product_description)s, %(price_wholesale)s, '
                          '%(datetime)s, %(price_value)s);', param)
    else:
        param = {'price_id': price['id'], 'datetime': datetime, 'price_value': price['value']}
        if 'description' in price:
            param['price_description'] = price['description']
        d6_cursor.execute('INSERT perla.price_history (price_id, price_description, price_value, datetime) VALUES '
                          '(%(price_id)s, %(price_description)s, %(price_value)s, %(datetime)s);', param)
    d6_cursor.execute('UPDATE perla.price SET value = %s WHERE id = %s LIMIT 1;',
                      (price['value'], price['id']))
    d6_cursor.close()


def handle_action_perla_attach_prices_at_product(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()
    product = msg['product']
    d6_cursor.execute('DELETE FROM perla.key_price WHERE product_sku = %s', (product['sku'],))
    if 'price' in msg:
        d6_cursor.execute('INSERT perla.key_price(product_sku, price_id) VALUES (%s, %s);',
                          (product['sku'], msg['price']['id']))
    elif 'prices' in msg and len(msg['prices']) == 2:
        for price in msg['prices']:
            key = None
            type_key = None
            if 'wholesale' in price and price['wholesale']:
                key = 156
                type_key = 2000

            d6_cursor.execute('INSERT perla.key_price(product_sku, price_id, `type_key`, `key`) VALUES '
                              '(%s, %s, %s, %s);', (product['sku'], price['id'], type_key, key))
    elif 'prices' in msg and len(msg['prices']) == 1:
        d6_cursor.execute('INSERT perla.key_price(product_sku, price_id) VALUES (%s, %s);',
                          (product['sku'], msg['prices'][0]['id']))
    d6_cursor.close()


def handle_action_perla_register_purchase_price(msg):
    provider = msg['provider']

    for k in list(provider.keys()):
        if k not in ['id', 'type', 'business_name', 'name']:
            del provider[k]

    purchase = msg['purchase']
    for k in list(purchase.keys()):
        if k not in ['id', 'type']:
            del purchase[k]

    purchase_price = dict()
    purchase_price['provider'] = provider
    purchase_price['purchase'] = msg['purchase']
    purchase_price['type'] = 'perla/purchase_price'
    if 'datetime' in msg:
        purchase_price['datetime'] = msg['datetime']
    else:
        purchase_price['datetime'] = datetime_isoformat(datetime.now())

    if 'my_item' in msg:
        pass
    elif 'my_items' in msg:
        myitems = msg['my_items']
        for myitem in myitems:
            purchase_price['id'] = get_id_with_name(purchase_price['type'])
            purchase_price['my_item'] = myitem

            purchase_price['value'] = myitem['price']
            del myitem['price']
            persist_bethesda_perla_purchase_price(purchase_price)
            price = {'id': purchase_price['id'], 'value': purchase_price['value'], 'type': purchase_price['type']}
            myitem['price'] = price

        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/get_items_factor_related',
               'query': {'items': myitems}}
        answer = agent_itzamara.send_msg(msg)
        myitems = answer['items']
        purchase_price['type'] = 'perla/purchase_price/disaggregated'
        for myitem in myitems:
            price_lowest = None
            for related in myitem['items_related']:
                if related['factor_type'] == 'lowest_common':
                    price_lowest = myitem['price']['value'] / related['factor']
                    break
            purchase_price['aggregate'] = {'my_item': {'sku': myitem['sku']}, 'price': {'id': myitem['price']['id']}}
            for related in myitem['items_related']:
                if related['factor_type'] == 'down':
                    purchase_price['id'] = get_id_with_name('perla/purchase_price/disaggregated')
                    purchase_price['value'] = myitem['price']['value'] / related['factor']
                    del related['factor']
                    del related['factor_type']
                    purchase_price['my_item'] = related
                    persist_bethesda_perla_purchase_price(purchase_price)
                elif related['factor_type'] == 'up':
                    purchase_price['id'] = get_id_with_name('perla/purchase_price/disaggregated')
                    purchase_price['value'] = myitem['price']['value'] * related['factor']
                    del related['factor']
                    del related['factor_type']
                    purchase_price['my_item'] = related
                    persist_bethesda_perla_purchase_price(purchase_price)
                elif related['factor_type'] == 'lowest':
                    purchase_price['id'] = get_id_with_name('perla/purchase_price/disaggregated')
                    purchase_price['value'] = price_lowest * related['factor']
                    del related['factor']
                    del related['factor_type']
                    purchase_price['my_item'] = related
                    persist_bethesda_perla_purchase_price(purchase_price)
                elif related['factor_type'] == 'lowest_common':
                    purchase_price['id'] = get_id_with_name('perla/purchase_price/disaggregated')
                    purchase_price['value'] = price_lowest
                    del related['factor']
                    del related['factor_type']
                    purchase_price['my_item'] = related
                    persist_bethesda_perla_purchase_price(purchase_price)
            del myitem['items_related']
        return {'my_items': myitems}


def handle_action_perla_register_provider_price_offer(msg):
    provider_price = dict()
    provider_price['id'] = get_id_with_name('perla/provider_offer_price')
    provider_price['type'] = 'perla/provider_price_offer'

    if 'my_item' in msg and 'sku' in msg['my_item'] and 'description' in msg['my_item']:
        provider_price['my_item'] = msg['my_item']
    elif 'item' in msg and isinstance(msg['item'], str):
        answer = agent_itzamara({'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': msg['item']}})
        if 'result' not in answer or answer['result'] is None:
            raise Exception('item not found')
        provider_price['my_item'] = answer['result']
    elif 'item' in msg and 'sku' in msg['item'] and 'description' in msg['item']:
        provider_price['my_item'] = msg['item']
    elif 'item' in msg and 'sku' in msg['item'] and 'description' not in msg['item']:
        answer = agent_itzamara({'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': msg['item']['sku']}})
        if 'result' not in answer or answer['result'] is None:
            raise Exception('item not found')
        provider_price['my_item'] = answer['result']
    elif 'sku' in msg:
        answer = agent_itzamara({'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': msg['sku']}})
        if 'result' not in answer or answer['result'] is None:
            raise Exception('item not found')
        provider_price['my_item'] = answer['result']
    else:
        raise Exception('item not found')
    if 'price' in msg:
        price = msg['price']
        if isinstance(price, dict) and 'value' in price:
            provider_price['value'] = price['value']
        elif isinstance(price, D):
            provider_price['value'] = price
        elif isinstance(price, int):
            provider_price['value'] = D(price)
        else:
            raise Exception('price not found')
    elif 'value' in msg:
        provider_price['value'] = msg['value']
    else:
        raise Exception('price not found')

    if 'provider' in msg:
        provider = msg['provider']
        if isinstance(provider, dict) and 'id' in provider and 'name' in provider:
            provider_price['provider'] = provider
        elif isinstance(provider, dict) and 'id' in provider and 'name' not in provider:
            answer = agent_piper({'type_message': 'find_one', 'type': 'piper/provider', 'query': {'id': provider['id']}})
            if 'result' not in answer or answer['result'] is None:
                raise Exception('provider nt found')
            provider_price['provider'] = answer['result']
        elif isinstance('provider', str):
            answer = agent_piper({'type_message': 'find_one', 'type': 'piper/provider', 'query': {'id': provider}})
            if 'result' not in answer or answer['result'] is None:
                raise Exception('provider nt found')
            provider_price['provider'] = answer['result']
    else:
        raise Exception('provider nt found')

    provider = provider_price['provider']

    for k in list(provider.keys()):
        if k not in ['id', 'name', 'type']:
            del provider[k]

    if 'provider_item' in msg:
        provider_price['provider_item'] = msg['provider_item']

    if 'datetime' in msg:
        provider_price['datetime'] = msg['datetime']
    else:
        provider_price['datetime'] = datetime_isoformat(datetime.now())

    dictutils.dec_to_float(provider_price)
    coll_provider_price_offer.insert(provider_price)
    del provider_price['_id']
    dictutils.float_to_dec(provider_price)
    answer = agent_itzamara.send_msg({'type_message': 'request',
                                      'request_type': 'get',
                                      'get': 'itzamara/items_factor_related',
                                      'query': {'item': provider_price['my_item']}})
    items_related = answer['item']['items_related']
    if len(items_related) == 0:
        return {'price': provider_price}
    prices = [deepcopy(provider_price)]

    lowest_price = None
    for item_related in items_related:
        if item_related['factor_type'] == 'lowest_common':
            lowest_price = provider_price['value'] / item_related['factor']
            break
    price_disaggregated = dict()
    price_disaggregated['type'] = 'perla/provider_offer_price/disaggregated'
    price_disaggregated['datetime'] = provider_price['datetime']
    price_disaggregated['provider'] = provider_price['provider']
    aggregate = {'my_item': provider_price['my_item'],
                 'price': {'id': provider_price['id']}}

    if 'provider_item' in provider_price:
        aggregate['provider_item'] = provider_price['provider_item']
    price_disaggregated['aggregate'] = aggregate
    for item_related in items_related:
        if item_related['factor_type'] in ['lowest_common', 'down']:
            price_disaggregated['id'] = get_id_with_name(price_disaggregated['type'])
            price_disaggregated['value'] = round(provider_price['value'] / item_related['factor'], 2)
            dictutils.dec_to_float(price_disaggregated)
            del item_related['factor_type']
            del item_related['factor']
            price_disaggregated['my_item'] = item_related
            coll_provider_price_offer.insert(price_disaggregated)
            del price_disaggregated['_id']
        elif item_related['factor_type'] == 'lowest':
            price_disaggregated['id'] = get_id_with_name(price_disaggregated['type'])
            price_disaggregated['value'] = round(lowest_price * item_related['factor'], 2)
            dictutils.dec_to_float(price_disaggregated)
            del item_related['factor_type']
            del item_related['factor']
            price_disaggregated['my_item'] = item_related
            coll_provider_price_offer.insert(price_disaggregated)
            del price_disaggregated['_id']
        elif item_related['factor_type'] == 'up':
            price_disaggregated['id'] = get_id_with_name(price_disaggregated['type'])
            price_disaggregated['value'] = round(provider_price['value'] * item_related['factor'], 2)
            dictutils.dec_to_float(price_disaggregated)
            del item_related['factor_type']
            del item_related['factor']
            price_disaggregated['my_item'] = item_related
            coll_provider_price_offer.insert(price_disaggregated)
            del price_disaggregated['_id']
        prices.append(deepcopy(price_disaggregated))
    if len(prices) == 1:
        return {'price': prices[0]}
    elif len(prices) > 1:
        return {'prices': prices}
    else:
        return {'error': False}


def handle_action_perla_change_price_value(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()

    def __help(p_id, value):
        d6_cursor.execute('UPDATE perla.price SET value = %s WHERE id = %s;', (value, p_id))
        d6_cursor.execute('SELECT DICTINCT product_sku FROM perla.key_price WHERE price_id = %s;', (p_id,))
        ll = list()
        for sku, in d6_cursor:
            ll.append(sku)
        return ll

    skus_altered = list()
    if 'actions' in msg:
        for action in msg['actions']:
            skus_altered += __help(action['price']['id'], action['value'])
    else:
        skus_altered += __help(msg['price']['id'], msg['value'])
    event = {'type_message': 'event', 'event': 'perla/price/value/updated', 'skus_updated': skus_altered}
    agent_ella.send_msg(event)
    d6_cursor.close()


def handle_event_perla_price_changed(msg):
    product_price_changed = list()
    for affected in msg['affected']:
        if 'product' in affected:
            product_price_changed.append(affected['product'])


def handle_find_perla_price(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()
    clauses = list()
    if 'query' in msg and 'item' in msg.query or 'sku' in msg.query:
        pass
    else:
        if 'query' in msg:
            for k1, v1 in msg['query'].items():
                if k1 == 'description':
                    if isinstance(v1, dict):
                        for k2, v2 in v1.items():
                            if k2 == '!like':
                                clauses.append('description LIKE \'%' + v2.replace(' ', '%').replace('\'', '\\\'') + '%\'')
        stmt = 'SELECT id COLLATE utf8_general_ci, description, value FROM perla.price'
        if len(clauses) > 0:
            stmt += ' WHERE ' + ' AND '.join(clauses)
        stmt += ';'
        d6_cursor.execute(stmt)
        result = list()
        for id, desc, value in d6_cursor:
            result.append({'id': id, 'description': desc, 'value': value})
    d6_cursor.close()
    return {'result': result}


def handle_find_perla_provider_price_offer(msg):
    filt = dict()
    for key, value in msg['query'].items():
        if key == 'my_item':
            if isinstance(value, dict):
                filt['my_item.sku'] = value['sku']
            elif isinstance(value, str):
                filt['my_item.sku'] = value
        elif key == 'item':
            if isinstance(value, dict):
                filt['my_item.sku'] = value.sku
    result = [r for r in coll_provider_price_offer.find(filt, {'_id': False})]
    return {'result': result}


def handle_find_perla_purchase_price(msg):
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    if 'my_item' in msg.query:
        sku = msg.query.my_item.sku
    elif 'item' in msg.query:
        sku = msg.query.item.sku
    else:
        raise Exception('query should contains item')
    d6_cursor.execute('SELECT * FROM perla.purchase_price WHERE local_item_sku = %s;', (sku,))
    result = [convert_purchase_price_maria_to_mongo(r) for r in d6_cursor]
    d6_cursor.close()
    return {'result': result}


def handle_find_one_perla_price(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()

    query = msg['query']

    if 'sku' in query:
        item_sku = query['sku']
    elif 'item' in query and 'sku' in query['item']:
        item_sku = query['item']['sku']
    else:
        raise Exception('find_one should contains item\'s sku')

    if 'wholesale' in query:
        wholesale = query['wholesale']
    elif 'client' in query and 'wholesale' in query['client']:
        wholesale = query['client']['wholesale']
    else:
        wholesale = False

    price = None
    if wholesale:
        d6_cursor.execute('SELECT price.id, price.value FROM perla.price INNER JOIN perla.key_price ON '
                          'price.id = key_price.price_id WHERE key_price.`key` = 156 AND key_price.type_key = 2000 '
                          'AND key_price.product_sku = %s LIMIT 1;',
                          (item_sku,))
        if d6_cursor.rowcount == 1:
            id, value = d6_cursor.fetchone()
            price = {'id': id, 'value': value, 'type': 'perla/price'}
    if price is None:
        d6_cursor.execute('SELECT price.id, price.value FROM perla.price INNER JOIN perla.key_price ON '
                          'price.id = key_price.price_id WHERE key_price.`key` IS NULL AND key_price.type_key IS NULL AND '
                          'key_price.product_sku = %s LIMIT 1;',
                          (item_sku,))
        if d6_cursor.rowcount == 1:
            id, value = d6_cursor.fetchone()
            price = {'id': id, 'value': value, 'type': 'perla/price'}
    d6_cursor.close()
    if price is not None and isinstance(price['id'], bytearray):
        price['id'] = str(price['id'], encoding='utf8')
    return {'result': price}


def handle_get_perla_get_benefit_of_new_purchase_prices(msg):
    stmt = '''SELECT purchase_price.id COLLATE utf8_general_ci, purchase_price.price_value, purchase_price.local_item_sku, \
purchase_price.local_item_description, price.id COLLATE utf8_general_ci, price.description, price.value, \
key_price.`key` FROM perla.purchase_price LEFT JOIN perla.key_price ON key_price.product_sku = \
purchase_price.local_item_sku lEFT JOIN perla.price ON price.id = key_price.price_id WHERE purchase_price.datetime = \
(SELECT MAX(datetime) FROM perla.purchase_price as bb WHERE bb.local_item_sku = purchase_price.local_item_sku) AND \
purchase_price.id IN (SELECT id FROM perla.purchase_price LEFT JOIN perla.last_purchase_price AS snapshot ON \
snapshot.sku = purchase_price.local_item_sku WHERE (purchase_price.price_value <> snapshot.value AND snapshot.datetime \
< purchase_price.datetime) OR local_item_sku NOT IN (SELECT sku FROM perla.last_purchase_price));'''

    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute(stmt)
    items = list()

    def get_item(i_s, i_d, _pp_id, _pp_value):
        for item in items:
            if item['product']['sku'] == i_s:
                return item
        item = {'product': {'sku': i_s, 'description': i_d}, 'purchase_price': {'id': _pp_id, 'value': _pp_value}}
        items.append(item)
        return item
    for pp_id, pp_value, item_sku, item_desc, p_id, p_desc, p_value, kk in d6_cursor:
        ii = get_item(item_sku, item_desc, pp_id, pp_value)
        if 'price' in ii and (p_id is not None and p_desc is not None):
            ii['price']['wholesale'] = kk is None
            prices = [ii['price']]
            price = {'id': p_id, 'description': p_desc, 'value': p_value, 'wholesale': kk is not None, 'benefit':
                round(((p_value / pp_value) - 1) * 100, 2)}
            prices.append(price)
            ii['prices'] = prices
            del ii['price']
        elif p_id is not None and p_desc is not None:
            ii['price'] = {'id': p_id, 'description': p_desc, 'value': p_value, 'benefit': \
                round(((p_value / pp_value) - 1) * 100, 2)}
    d6_cursor.close()
    return {'items': items}


def handle_get_perla_prices_attached(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()
    r = d6_cursor.execute('SELECT price.id COLLATE utf8_general_ci, price.description, price.value, key_price.type_key \
FROM perla.price RIGHT JOIN perla.key_price ON key_price.price_id = price.id WHERE key_price.product_sku = %s;',
                          (msg['product']['sku'],))
    answer = dict()
    if r > 1:
        prices = list()
        for id, desc, value, key in d6_cursor:
            prices.append({'id': id, 'description': desc, 'value': value, 'wholesale': key is not None})
        answer['prices'] = prices
    elif r == 1:
        id, desc, value, key = d6_cursor.fetchone()
        answer['price'] = {'id': id, 'description': desc, 'value': value}
    d6_cursor.close()
    return answer


def handle_get_perla_provider_sells(msg):
    provider = msg['provider']
    cc = coll_provider_price_offer.find({'provider.id': provider['id'], 'type': 'perla/provider_price_offer'},
                                        {'_id': False, 'my_item': True})
    result = list()
    for price in cc:
        item = price['my_item']
        for res in result:
            if item['sku'] == res['sku']:
                break
        else:
            result.append(item)
    return {'result': result}


def handle_get_perla_price(msg):
    query = msg.query
    if 'store' in query and isinstance(query.store, dict) and 'id' in query.store:
        store_id = query.store.id
    elif 'store' in query and isinstance(query.store, str):
        store_id = query.store
    else:
        store_id = None

    if 'wholesale' in query:
        wholesale = query.wholesale
    elif 'client' in query and isinstance(query.client, dict) and 'wholesale' in query.client:
        wholesale = query.client.wholesale
    else:
        wholesale = False

    if 'sku' in query:
        item_sku = query.sku
    elif 'item' in query and 'sku' in query.item:
        item_sku = query.item.sku
    else:
        raise Exception('query should contains item.sku')

    d5_session = d5.session()

    price = None
    if wholesale:
        rr = d5_session.run('match (item{sku:{item_sku}})-[:price{wholesale:true}]->(price) '
                            'return price.id as price_id, labels(price) as labels limit 1', {'item_sku': item_sku})
        rc = rr.single()
        if rc is not None:
            price = dict({'id': rc['price_id'], 'labels': rc['labels']})
    else:
        rr = d5_session.run('match (item{sku:{item_sku}})-[rel:price]->(price) '
                            'where not exists(rel.wholesale) or rel.wholesale = false '
                            'return price.id as price_id , labels(price) as labels limit 1', {'item_sku': item_sku})
        rc = rr.single()
        if rc is not None:
            price = dict({'id': rc['price_id'], 'labels': rc['labels']})

    if price is not None:
        if 'perla_price' in price.labels:
            price.type = 'perla/price'
            del price.labels
        elif 'perla_scale_prices' in price.labels:
            price.type = 'perla/scale_prices'
            del price.labels
        else:
            d5_session.close()
            raise Exception('price should contains aleast a label of price')
        if price.type == 'perla/price':
            d6.ping(True)
            d6_cursor = d6.cursor()
            r = d6_cursor.execute('select value, description from perla.price where id = %s limit 1;', (price.id, ))
            if r == 1:
                value, desc = d6_cursor.fetchone()
                price.value = value
                price.description = desc
            else:
                price = None
            d6_cursor.close()
        elif price.type == 'perla/scale_prices':
            price = coll_scale_prices.find_one({'id': price.id}, {'_id': False})
    d5_session.close()
    return {'result': price}


rr = Pool_Handler()

rr.reg('type_message=action.action=perla/attach_price_at_product', handle_action_perla_attach_prices_at_product)
rr.reg('type_message=action.action=perla/attach_prices_at_product', handle_action_perla_attach_prices_at_product)
rr.reg('type_message=action.action=perla/register_provider_price_offer',
       handle_action_perla_register_provider_price_offer)
rr['type_message=action.action=perla/create_provider_price_offer'] = handle_action_perla_register_provider_price_offer
rr.reg('type_message=action.action=perla/register_purchase_price', handle_action_perla_register_purchase_price)
rr.reg('type_message=find.type=perla/price', handle_find_perla_price)
rr.reg('type_message=find.type=perla/provider_offer_price', handle_find_perla_provider_price_offer)
rr.reg('type_message=find.type=perla/provider_price_offer', handle_find_perla_provider_price_offer)
rr.reg('type_message=find.type=perla/purchase_price', handle_find_perla_purchase_price)
rr['type_message=find_one.type=perla/price'] = handle_find_one_perla_price
rr.reg('type_message=request.request_type=get.get=perla/get_benefit_of_new_purchase_prices',
       handle_get_perla_get_benefit_of_new_purchase_prices)
rr['type_message=request.request_type=get.get=perla/prices_attached'] = handle_get_perla_prices_attached
rr.reg('type_message=request.request_type=get.get=perla/provider_sells', handle_get_perla_provider_sells)

if __name__ == '__main__' and True:
    print("I'm perla")
    recipient = Recipient()
    recipient.prepare("/perla", rr)
    recipient.begin_receive_forever()
