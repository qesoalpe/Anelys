from dict import Dict as dict
from pymongo import MongoClient
import pymysql
from neo4j.v1 import GraphDatabase, basic_auth


d1 = MongoClient(username='anelys', password='Abc123456!', document_class=dict)

d5 = GraphDatabase.driver('bolt://127.0.0.1', auth=basic_auth('alejandro', '47exI4'))

d6_config = dict({'host': '127.0.0.1', 'port': 3306, 'user': 'anelys', 'autocommit': True})

d6 = pymysql.connect(**d6_config)

citlali_maria_config = {'host': '127.0.0.1', 'port': 8801, 'user': 'citlali', 'password': 'que_cantann',
                        'autocommit': True}

citlali_maria = pymysql.connect(**citlali_maria_config)
