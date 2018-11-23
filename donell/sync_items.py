from pymongo import MongoClient
from neo4j.v1 import GraphDatabase, basic_auth
from dict import Dict
from utils import find_one
from copy import deepcopy

d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

d1.admin.authenticate('alejandro', '47exI4')
d5_session = d5.session()

consumed = list()
produced = list()

for production in d1.donell.production.find({}, {'produced': True, 'consumed': True, '_id': False}):
    for item in production['produced']:
        if find_one(lambda x: item.sku == x.sku, produced) is None:
            item = deepcopy(item)
            for k in list(item.keys()):
                if k not in ['sku', 'description']:
                    del item[k]
            produced.append(item)

    for item in production['consumed']:
        if find_one(lambda x: item.sku == x.sku, consumed) is None:
            item = deepcopy(item)
            for k in list(item.keys()):
                if k not in ['sku', 'description']:
                    del item[k]
            consumed.append(item)

rr = d5_session.run('match (producer{id:\'42-3\'}) match (item) '
                    'where item.sku in {items_sku} and not ((producer)-[:produces]->(item)) '
                    'create unique (producer)-[:produces]->(item);',
                   {'items_sku': [item.sku for item in produced]})
rr.single()

rr = d5_session.run('match (consumer{id:\'42-3\'}) match (item) '
                    'where item.sku in {items_sku} and not ((consumer)-[:consumes]->(item)) '
                    'create unique (consumer)-[:consumes]->(item);',
                    {'items_sku': [item.sku for item in consumed]})
rr.single()
