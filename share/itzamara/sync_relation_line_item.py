from neo4j.v1 import GraphDatabase, basic_auth
from dict import Dict

d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

d5_session = d5.session()
rr = d5_session.run('match (line:itzamara_line)<-[rel:line]-() where exists(rel.type) delete rel')

rr.single()

rr = d5_session.run('match (line:itzamara_line)<-[rel:line]-(item) where exists(item.sku) and exists(item.description) '
                    'and not exists(rel.type) '
                    'return item.sku as sku, item.description as description, line.id as line_id')

items = [Dict({'sku': rc['sku'], 'description': rc['description'], 'line_id': rc['line_id']}) for rc in rr]

from itzamara.remote import get_items_factor_related
items = get_items_factor_related(items)

for item in items:
    if 'items_related' in item:
        for itemrelated in item.items_related:

            rr = d5_session.run('match (item{sku:{sku}}) match (line{id:{line_id}}) '
                                'where not ((item)-[:line]->(:itzamara_line))'
                                'create unique (line)<-[rel:line]-(item) '
                                'set rel.type = \'inherited\', rel.inherited_from = {parent};',
                                {'sku': itemrelated.sku, 'line_id': item.line_id, 'parent': item.sku})
            rr.single()
