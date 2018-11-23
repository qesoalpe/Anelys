#! /usr/bin/env python3
import pymysql
from sarah.acp_bson import Client
import isodate
import datetime
from decimal import Decimal

storage = {'id': '42-3'}

d8757_6 = pymysql.connect(host='192.168.1.104', port=3305, user='alejandro', password='5175202', autocommit=True)
d6_cursor = d8757_6.cursor(cursor=pymysql.cursors.DictCursor)
agent_itzamara = Client('valentine.sync_itemdemand', 'itzamara')

itemsdemand = list()
d6_cursor.execute('SELECT distinct item.sku as sku, item.description as description from itzamara.item inner join '
                  'valentine.method_evaluation_supply as method on method.item_sku = item.sku WHERE method.method = '
                  '"itemdemand" and storage_id = %s;', (storage['id'],))

for item in d6_cursor:
    itemsdemand.append(item)

msg = {'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/items_factor_related',
       'query': {'items': itemsdemand}}

answer = agent_itzamara(msg)
itemsdemand = answer['items']
end = datetime.date.today() - datetime.timedelta(days=1)
period = isodate.parse_duration('P15D')
start = end - period
d6_cursor = d8757_6.cursor()

for itemdemand in itemsdemand:
    d6_cursor.execute('SELECT IFNULL(SUM(quanty), 0) FROM serena.item_sold_daily WHERE date BETWEEN %s and %s and '
                      'item_sku = %s and store_id = %s', (start, end, itemdemand['sku'], storage['id']))
    itemdemand['demand'], = d6_cursor.fetchone()
    for itemrelated in itemdemand['items_related']:
        d6_cursor.execute('SELECT IFNULL(SUM(quanty), 0) FROM serena.item_sold_daily WHERE date between %s and %s and '
                          'item_sku = %s and store_id = %s', (start, end, itemrelated['sku'], storage['id']))
        itemrelated['demand'], = d6_cursor.fetchone()


def set_demand_absolut(_item):
    _item['demand_absolut'] = _item['demand']
    if 'items_related' in _item:
        demand_factorized = Decimal()
        for _itemrelated in _item['items_related']:
            if _itemrelated['factor_type'] == 'lowest_common':
                if _itemrelated['demand'] > Decimal():
                    demand_factorized += _itemrelated['demand'] / _itemrelated['factor']
                lowestcommonfactor = _itemrelated['factor']
                break
        else:
            lowestcommonfactor = None
        for _itemrelated in _item['items_related']:
            if _itemrelated['factor_type'] == 'up':
                demand_factorized += _itemrelated['demand'] * _itemrelated['factor']
            elif _itemrelated['factor_type'] == 'down':
                if _itemrelated['demand'] > Decimal():
                    demand_factorized += _itemrelated['demand'] / _itemrelated['factor']
            elif _itemrelated['factor_type'] == 'lowest':
                if _itemrelated['demand'] > Decimal():
                    demand_factorized += (_itemrelated['demand'] / lowestcommonfactor) * _itemrelated['factor']
        _item['demand_absolut'] += demand_factorized
    _item['demand_absolut'] = round(_item['demand_absolut'], 3)

d6_cursor.execute('delete from valentine.item_demand where storage_id = %s;', (storage['id'],))
for item in itemsdemand:
    set_demand_absolut(item)
    result = d6_cursor.execute('insert into valentine.item_demand (item_sku, item_description, period, demand, '
                               'storage_id, storage_type) VALUES (%(item_sku)s, %(item_description)s, %(period)s, '
                               '%(demand)s, %(storage_id)s, "valentine/storage") ON DUPLICATE KEY UPDATE demand = '
                               'values(demand), period = VALUES(period);',
                               {'item_sku': item['sku'], 'item_description': item['description'],
                                'period': isodate.duration_isoformat(period),
                                'demand': item['demand_absolut'], 'storage_id': storage['id']})
d6_cursor.close()
d8757_6.close()
print('ready')
