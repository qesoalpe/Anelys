import pymysql
from neo4j.v1 import GraphDatabase, basic_auth

d8757_5 = GraphDatabase.driver('bolt://quecosas.ddns.net', auth=basic_auth('alejandro', '47exI4'))
d8757_6 = pymysql.connect(host='quecosas.ddns.net', port=3305, user='alejandro', password='5175202')

d6_cursor = d8757_6.cursor()
d5_session = d8757_5.session()

rr = d5_session.run('MATCH (:itzamara_item)-[rel:pack]-(:itzamara_item) delete rel;')
rr = d6_cursor.execute('select item_factor_id, item_pack_id, factor FROM itzamara.item_pack')
for item_factor, item_pack, quanty in d6_cursor:
    quanty = int(quanty)
    rr = d5_session.run('match (pack:itzamara_item{sku:{pack_sku}}) '
                        'match (item:itzamara_item{sku:{item_sku}}) '
                        'CREATE UNIQUE (pack)-[:pack{quanty:{quanty}}]->(item);',
                        {'pack_sku': item_pack, 'item_sku': item_factor, 'quanty': quanty})
    rr = rr.single()
print('done')
