from sarah.acp_bson import Client
from sarah import dictutils
from neo4j.v1 import GraphDatabase, basic_auth
from decimal import Decimal
import isodate
from copy import deepcopy
from katherine import d6_config, pymysql
from pprint import pprint

storage = {'id': '42-3', 'type': 'valentine/storage'}


supplier = {'id': '61-3', 'type': 'piper/provider'}

reorder_point_demand = 'P30D'
maximum_demand_cover = 'P45D'

if isinstance(reorder_point_demand, str):
    reorder_point_demand = isodate.parse_duration(reorder_point_demand)

if isinstance(maximum_demand_cover, str):
    maximum_demand_cover = isodate.parse_duration(maximum_demand_cover)


periodminimum = reorder_point_demand
periodmaximum = maximum_demand_cover

agent_piper = Client('alejandro', 'piper')
agent_itzamara = Client('alejandro', 'itzamara')
agent_valentine = Client('alejandro', 'valentine')


d8757_6 = pymysql.connect(**d6_config)


d6_cursor = d8757_6.cursor(pymysql.cursors.DictCursor)
d8757_5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))
d5_session = d8757_5.session()


def add_items(left: list, right: list) -> list:
    res = list()
    for ll in left:
        for rr in res:
            if rr['sku'] == ll['sku']:
                break
        else:
            res.append(ll)
    for rg in right:
        for rs in res:
            if rs['sku'] == rg['sku']:
                break
        else:
            res.append(rg)
    return res


def subtract_items(left, right):
    res = list()
    for ll in left:
        for rr in res:
            if rr['sku'] == ll['sku']:
                break
        else:
            res.append(ll)
    for rg in right:
        for rs in res[:]:
            if rs['sku'] == rg['sku']:
                res.remove(rs)
                break
    return res


def operator_and_items(left, right):
    res = list()
    for l in left:
        for r in right:
            if l['sku'] == r['sku']:
                for rs in res:
                    if l['sku'] == rs['sku']:
                        break
                else:
                    res.append(l)
                break
    return res


def add_skus(left, right):
    result = list()
    for lf in left:
        if lf not in result:
            result.append(lf)

    for rg in right:
        if rg not in result:
            result.append(rg)
    return result


def subtract_skus(left, right):
    result = list()
    for lf in left:
        if lf not in result:
            result.append(lf)
    for rg in right:
        if rg in result:
            result.remove(rg)
    return result


def operator_and_skus(left, right):
    result = list()
    for lf in left:
        if lf in right and lf not in result:
            result.append(lf)
    return result


def operator_or_skus(left, right):
    result = list()
    for lf in left:
        if lf not in result:
            result.append(lf)
    for rg in right:
        if rg not in result:
            result.append(rg)
    return result


def operator_xor_skus(left, right):
    result = list()
    for lf in left:
        if lf not in result and lf not in right:
            result.append(lf)
    for rg in right:
        if rg not in result and rg not in left:
            result.append(rg)
    return result


def get_skus_supplier_stores(_supplier):
    rr = d5_session.run('match ({id:{supplier_id}})-[:stores]->(item) with distinct item return item.sku as sku;',
                        {'supplier_id': _supplier['id']})
    skus = list()
    for rc in rr:
        if rc['sku'] is not None:
            skus.append(rc['sku'])
    return skus


def get_skus_piper_provider_not_sells(_provider):
    answer = agent_piper({'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_not_sells',
                          'provider': _provider})
    result = list()
    for rr in answer['result']:
        result.append(rr['sku'])
    return result


def get_skus_piper_provider_sells(_provider):
    answer = agent_piper({'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_sells',
                          'provider': _provider})
    result = list()
    for rr in answer['result']:
        result.append(rr['sku'])
    return result


def get_skus_valentine_storage_supplies(_storage):
    _d6_cursor = d8757_6.cursor()
    _d6_cursor.execute('select distinct item.sku as sku from itzamara.item inner join valentine.method_evaluation_supply as method on method.item_sku = item.sku where method.storage_id = %s;', (_storage['id'],))
    result = list()
    for sku, in _d6_cursor:
        result.append(sku)
    return result


def get_items_piper_provider_not_sells(_provider, factorrelateds=True):
    answer = agent_piper({'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_not_sells',
                          'provider': _provider})
    result = answer['result']
    if factorrelateds:
        answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'v': 1,
                                 'get': 'itzamara/items_factor_related', 'items': result})
        return answer['items']
    else:
        return result


def get_items_piper_provider_sells(_provider, factorrelateds=True):
    answer = agent_piper({'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_sells',
                          'provider': _provider})
    result = answer['result']
    if factorrelateds:
        answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'v': 1,
                                 'get': 'itzamara/items_factor_related', 'items': result})
        return answer['items']
    else:
        return result


def get_items_supplier_supplies_at_storage(_supplier, factorrelateds=True, _storage=None):
    if _storage is None:
        _storage = storage

    _d6_cursor = d8757_6.cursor(pymysql.cursors.DictCursor)
    _d6_cursor.execute('select distinct item.sku as sku, item.description as description from itzamara.item right join valentine.method_evaluation_supply as method on method.item_sku = item.sku where method.storage_id = %s and method.supplier_id = %s;', (_storage['id'], _supplier['id']))
    result = list()
    for item in _d6_cursor:
        result.append(item)
    if factorrelateds:
        answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'v': 1,
                                 'get': 'itzamara/items_factor_related', 'items': result})
        return answer['items']
    else:
        return result


def get_items_valentine_storage_supplies_in(_storage=None, omit_predefined=True, factorrelateds=True):
    if _storage is None:
        _storage = storage
    if omit_predefined:
        d6_cursor.execute(
            'select distinct item.sku as sku, item.description as description from itzamara.item inner join valentine.method_evaluation_supply as method on method.item_sku = item.sku where method.storage_id = %s and supplier_id is null;',
            (_storage['id'],))
    else:
        d6_cursor.execute('select distinct item.sku as sku, item.description as description from itzamara.item inner join valentine.method_evaluation_supply as method on method.item_sku = item.sku where method.storage_id = %s;', (_storage['id'],))
    result = list()
    for item in d6_cursor:
        result.append(item)
    if factorrelateds:
        answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'v': 1,
                                 'get': 'itzamara/items_factor_related', 'items': result})
        return answer['items']
    else:
        return result


def get_items_supplier_stores(_supplier, factorrelateds=True):
    rr = d5_session.run('match ({id:{id}})-[:stores]->(item) with distinct item return item.sku as sku, item.description as description', {'id': _supplier['id']})
    result = list()
    for rc in rr:
        if rc['sku'] is not None and rc['description'] is not None:
            result.append({'sku': rc['sku'], 'description': rc['description']})
    if factorrelateds:
        answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
                                 'items': result})
        return answer['items']
    else:
        return result

if supplier['id'] == '28-3':
    storage_supplies_in = get_items_supplier_supplies_at_storage(supplier)
    supplier_stores = get_items_supplier_stores(supplier)
    items_suggested_to_supply = operator_and_items(storage_supplies_in, supplier_stores)

elif supplier['id'] in ['61-10', '61-3']:
    provider_not_sells = get_items_piper_provider_not_sells(supplier)

    provider_supplies_at_storage = get_items_supplier_supplies_at_storage(supplier)

    storage_supplies_in = get_items_valentine_storage_supplies_in(storage)

    items_suggested_to_supply = subtract_items(add_items(provider_supplies_at_storage, storage_supplies_in), provider_not_sells)

elif supplier['id'] in ['57-7', '61-12', '61-1']:
    provider_sells = get_items_piper_provider_sells(supplier)

    provider_not_sells = get_items_piper_provider_not_sells(supplier)

    supplier_supplies_at_storage = get_items_supplier_supplies_at_storage(supplier)

    storage_supplies_in = get_items_valentine_storage_supplies_in()

    items_suggested_to_supply = operator_and_items( add_items(supplier_supplies_at_storage, storage_supplies_in), subtract_items(provider_sells, provider_not_sells))
else:
    items_suggested_to_supply = get_items_valentine_storage_supplies_in(omit_predefined=True)
    if 'type' in supplier and supplier['type'] == 'piper/provider':
        provider_not_sells = get_items_piper_provider_not_sells(supplier)
        items_suggested_to_supply = subtract_items(items_suggested_to_supply, provider_not_sells)


for item in items_suggested_to_supply:
    if 'items_related' in item:
        break
else:
    answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
                             'query': {'items': items_suggested_to_supply}})
    items_suggested_to_supply = answer['items']


x = list()
_d6_cursor = d8757_6.cursor(pymysql.cursors.DictCursor)
_d6_cursor.execute('select method.item_sku, method.method, maximum, reorder_point, maximum_demand_cover, reorder_point_demand, itemdemand.period as period, itemdemand.demand as demand from valentine.method_evaluation_supply as method left join valentine.item_demand as itemdemand on itemdemand.item_sku = method.item_sku and method.storage_id = itemdemand.storage_id where method.storage_id = %s and supplier_id = %s;', (storage['id'], supplier['id']))
item_methods = list()

for item_method in _d6_cursor:
    item_methods.append(item_method)


def _help(_item, _item_method):
    _item = deepcopy(_item)
    for k in ['method', 'maximum', 'reorder_point', 'maximum_demand_cover', 'reorder_point_demand', 'period', 'demand']:
        if k in _item_method and _item_method[k] is not None:
            _item[k] = _item_method[k]
    if 'items_related' in _item:
        del _item['items_related']
    x.append(_item)


for item in items_suggested_to_supply[:]:
    for item_method in item_methods:
        if item_method['item_sku'] == item['sku']:
            _help(item, item_method)
            items_suggested_to_supply.remove(item)
            break
        elif 'items_related' in item:
            certain = False
            for ii in item['items_related']:
                if ii['sku'] == item_method['item_sku']:
                    _help(ii, item_method)
                    certain = True
                    items_suggested_to_supply.remove(item)
                    break
            if certain: break

_d6_cursor.execute('select method.item_sku, method.method, maximum, reorder_point, maximum_demand_cover, reorder_point_demand, itemdemand.period as period, itemdemand.demand as demand from valentine.method_evaluation_supply as method left join valentine.item_demand as itemdemand on itemdemand.item_sku = method.item_sku and method.storage_id = itemdemand.storage_id where method.storage_id = %s and supplier_id is NULL;', (storage['id'],))
item_methods = list()
for item_method in _d6_cursor:
    item_methods.append(item_method)
for item in items_suggested_to_supply[:]:
    for item_method in item_methods:
        if item_method['item_sku'] == item['sku']:
            _help(item, item_method)
            items_suggested_to_supply.remove(item)
            break
        elif 'items_related' in item:
            certain = False
            for ii in item['items_related']:
                if ii['sku'] == item_method['item_sku']:
                    _help(ii, item_method)
                    certain = True
                    items_suggested_to_supply.remove(item)
                    break
            if certain: break



if len(items_suggested_to_supply):
    for item in items_suggested_to_supply:
        x.append(item)
items_suggested_to_supply = x
for item in items_suggested_to_supply:
    if 'items_related' in item:
        del item['items_related']

answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
                         'items': items_suggested_to_supply})

items_suggested_to_supply = answer['items']

answer = agent_valentine({'type_message': 'request', 'request_type': 'get', 'get': 'valentine/inventory_absolut',
                          'storage': storage, 'items': items_suggested_to_supply})

items_suggested_to_supply = answer['items']


for item in items_suggested_to_supply[:]:
    if 'inventory_absolut' in item:
        item['inventory'] = item['inventory_absolut']
        del item['inventory_absolut']
        if 'items_related' in item:
            for ii in item['items_related']:
                for k in ['inventory', 'inventory_absolut']:
                    if k in ii:
                        del ii[k]

    if 'method' in item:
        if item['method'] == 'maximum':
            if item['reorder_point'] < item['inventory']:
                items_suggested_to_supply.remove(item)
            else:
                item['supply_suggested'] = item['maximum'] - item['inventory']

        elif item['method'] == 'itemdemand':
            if 'reorder_point_demand' in item:
                reorder_point_demand = item['reorder_point_demand']
            else:
                reorder_point_demand = periodminimum
            if 'maximum_demand_cover' in item:
                maximum_demand_cover = item['maximum_demand_cover']
            else:
                maximum_demand_cover = periodmaximum

            if isinstance(reorder_point_demand, str):
                reorder_point_demand = isodate.parse_duration(reorder_point_demand)
            if isinstance(maximum_demand_cover, str):
                maximum_demand_cover = isodate.parse_duration(maximum_demand_cover)

            if isinstance(item['period'], str):
                item['period'] = isodate.parse_duration(item['period'])

            if item['demand'] != Decimal():
                item['covered'] = item['period'] * float(item['inventory'] / item['demand'])
                if item['covered'] >= reorder_point_demand:
                    items_suggested_to_supply.remove(item)
                else:
                    item['supply_suggested'] = round(Decimal(((maximum_demand_cover - item['covered']) / item['period']) * float(item['demand'])), 3)
                    if item['supply_suggested'] < Decimal():
                        items_suggested_to_supply.remove(item)

if 'type' in supplier and supplier['type'] == 'piper/provider':
    items_provider_sells = get_items_piper_provider_sells(supplier)

    x = list()

    for item in items_suggested_to_supply[:]:
        for item_provider_sells in items_provider_sells:
            if item_provider_sells['sku'] == item['sku']:
                if 'items_related' in item: del item['items_related']
                x.append(item)
                items_suggested_to_supply.remove(item)
                break
        else:
            if 'items_related' in item:
                for item_related in item['items_related']:
                    for item_provider_sells in items_provider_sells:
                        if item_related['sku'] == item_provider_sells['sku']:
                            for it_rel in item['items_related']:
                                if it_rel['factor_type'] == 'lowest_common':
                                    lowest_common_factor = it_rel['factor']
                                    break
                            else:
                                lowest_common_factor = None
                            if item_related['factor_type'] == 'up':
                                item_related['inventory'] = item['inventory'] / item_related['factor']
                                if 'supply_suggested' in item:
                                    item_related['supply_suggested'] = item['supply_suggested'] / item_related['factor']
                            elif item_related['factor_type'] in ['down', 'lowest_common']:
                                item_related['inventory'] = item['inventory'] * item_related['factor']
                                if 'supply_suggested' in item:
                                    item_related['supply_suggested'] = item['supply_suggested'] * item_related['factor']
                            elif item_related['factor_type'] == 'lowest':
                                try:
                                    item_related['inventory'] = (item['inventory'] * lowest_common_factor) / item_related['factor']
                                    if 'supply_suggested' in item:
                                        item_related['supply_suggested'] = (item['supply_suggested'] * lowest_common_factor) / item_related['factor']
                                except:
                                    pprint(item_related)
                                    pprint(item)
                            x.append(item_related)
                            if item in items_suggested_to_supply:
                                items_suggested_to_supply.remove(item)
                            break
    items_suggested_to_supply = x

for item in items_suggested_to_supply:
    for k in ['items_related', 'factor', 'factor_type']:
        if k in item:
            del item[k]

for item in items_suggested_to_supply:
    if 'period' in item:
        item['period'] = isodate.duration_isoformat(item['period'])
    if 'covered' in item:
        item['covered'] = isodate.duration_isoformat(item['covered'])
    if 'items_related' in item:
        del item['items_related']


dictutils.list_dec_to_float(items_suggested_to_supply)

pprint(items_suggested_to_supply)


import json
f = open(r'D:\home\picazo\supply.json', 'wt', encoding='utf8')
json.dump(items_suggested_to_supply, f, indent=2)
f.close()

import csv
f = open(r'D:\home\picazo\supply.csv', 'wt', encoding='utf8', newline='')

writer = csv.DictWriter(f, ['sku', 'description', 'inventory', 'supply_suggested'])

writer.writeheader()

for item in items_suggested_to_supply:
    row = {'sku': item['sku'], 'description': item['description']}
    row['inventory'] = item['inventory'] if 'inventory' in item else None
    # row['covered'] = item['covered'] if 'covered' in item else None
    row['supply_suggested'] = item['supply_suggested'] if 'supply_suggested' in item else item['suply_suggested'] if 'suply_suggested' in item else None
    writer.writerow(row)

f.close()
