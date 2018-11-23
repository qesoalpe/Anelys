import pymysql
from neo4j.v1 import GraphDatabase, basic_auth
from katherine import d6_config
import os

if __name__ != '__main__':
    os.chdir(os.path.abspath(os.path.dirname(__file__)))


d8757_5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))
d8757_6 = pymysql.connect(**d6_config)

d6_cursor = d8757_6.cursor(pymysql.cursors.DictCursor)
d5_session = d8757_5.session()
r = d6_cursor.execute('select sku, description, modified, created from itzamara.item;')

items = list()
items_sku_d6 = list()
items_sku_d5 = list()
for item in d6_cursor:
    items.append(item)
    items_sku_d6.append(item['sku'])
    rr = d5_session.run('MERGE (item{sku:{item_sku}}) SET item :itzamara_item, item += {item};',
                        {'item_sku': item['sku'], 'item': item})

rr = d5_session.run('match (item:itzamara_item) return item.sku as item_sku;')
for rec in rr:
    items_sku_d5.append(rec['item_sku'])
deleted = list()
for sku in items_sku_d5:
    if sku not in items_sku_d6:
        rr = d5_session.run('match (item{sku:{sku}}) optional match (item)-[rel]-() delete rel, item;', {'sku': sku})
        deleted.append(sku)

from pprint import pprint

pprint(deleted)

rr = d5_session.run('match (:itzamara_item)-[rel:pack]-(:itzamara_item) delete rel;')
rr = rr.single()
d6_cursor.execute('select * from itzamara.item_pack;')
for item_pack in d6_cursor:
    rr = d5_session.run('match (item{sku:{item_sku}}) '
                        'match (pack{sku:{pack_sku}}) '
                        'create unique (pack)<-[:pack{quanty:{pack_quanty}}]-(item);',
                        {'item_sku': item_pack['item_factor_id'], 'pack_sku': item_pack['item_pack_id'],
                         'pack_quanty': float(item_pack['factor'])})
    rr.single()
print('ready')
