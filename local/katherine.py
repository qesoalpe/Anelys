from dict import Dict
from pymongo import MongoClient
import pymysql
from neo4j.v1 import GraphDatabase, basic_auth

dev = False

if dev:
    d1 = MongoClient(document_class=Dict)
    d6_config = {'host': '127.0.0.1', 'user': 'picazo', 'password': '5175202', 'autocommit': True}
    d5 = GraphDatabase.driver('bolt://127.0.0.1', auth=basic_auth('neo4j', '12345'))
    d6 = pymysql.connect(**d6_config)
else:

    d1 = MongoClient('mongodb://192.168.1.104', document_class=Dict,
                     username='picazo', password='47exI4', authSource='admin')

    try:
        d5 = GraphDatabase.driver('bolt://comercialpicazo.com',
                                  auth=basic_auth('alejandro', '47exI4'))
    except:
        d5 = None

    d6_config = {'host': 'comercialpicazo.com', 'port': 3306, 'user': 'picazo', 'password': '5175202',
                 'autocommit': True}

    d6 = pymysql.connect(**d6_config)

d2 = MongoClient('mongodb://comercialpicazo.com', port=27030,
                 username='picazo', password='47exI4', authSource='admin')

citlali_mongo = MongoClient(port=27020, document_class=Dict)

citlali_maria_config = {'host': '127.0.0.1', 'port': 8801, 'user': 'citlali', 'password': 'que_cantann',
                        'autocommit': True}

try:
    citlali_maria = pymysql.connect(**citlali_maria_config)
except:
    citlali_maria = None
