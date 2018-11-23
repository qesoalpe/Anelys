from dict import Dict
from pymongo import MongoClient
import pymysql
from utils import find_one
from neo4j.v1 import GraphDatabase, basic_auth


d6_config = {'host': 'comercialpicazo.com', 'port': 3306, 'user': 'picazo', 'password': '5175202',
             'autocommit': True}

# d6_config = {'host': '127.0.0.1', 'user': 'picazo', 'password': '5175202', 'autocommit': True}

citlali_maria_config = {'host': '127.0.0.1', 'port': 8801, 'user': 'citlali', 'password': 'que_cantann',
                        'autocommit': True}


d1 = MongoClient('mongodb://192.168.1.104', document_class=Dict,
                 username='picazo', password='47exI4', authSource='admin')
d1 = MongoClient(document_class=Dict)

try:
    d5 = GraphDatabase.driver('bolt://comercialpicazo.com',
                              auth=basic_auth('alejandro', '47exI4'))
except:
    d5 = None

d5 = GraphDatabase.driver('bolt://127.0.0.1', auth=basic_auth('neo4j', '12345'))
d6 = pymysql.connect(**d6_config)


coll_database_authorization = d1.katherine.database_authorization

citlali_mongo = MongoClient(port=27020, document_class=Dict)

_users = list()
try:
    citlali_maria = pymysql.connect(**citlali_maria_config)
except:
    citlali_maria = None


def get_id(user):
    if isinstance(user, (Dict,)) and 'type' in user and user.type == 'anelys/system':
        if 'id' in user and 'path' in user:
            return user.id + user.path
        elif 'id' in user and 'path' not in user:
            return user.id


def method_default(user, password):
    if isinstance(user, Dict) and 'not' in user:
        raise Exception('user requires id')
    elif isinstance(user, str):
        user = d1.katherine.user.find_one({'name': user}, {'_id': False})
        if user is None:
            raise Exception('user.name not found')

    d6 = pymysql.connect(**d6_config)
    d6_cursor = d6.cursor()
    r = d6_cursor.execute('select salt, hash from katherine.identification where user_id = %s limit 1;', (user.id, ))
    if r == 0:
        return
    salt, hash = d6_cursor.fetchone()
    import hashlib
    sha512 = hashlib.sha512()
    sha512.update((password + salt).encode('utf8'))
    response = sha512.hexdigest().upper() == hash
    d6_cursor.close()
    d6.close()
    return response


def login(user, password=None):
    if isinstance(user, (Dict,)) and 'type' in user and user.type == 'anelys/system':
        id = get_id(user)
        if id is None:
            raise Exception('id not in user: anelys/system')

        _user = find_one(lambda x: x.id == id, _users)
        if _user is None:
            _user = Dict({'id': id, 'type': user.type})
            _users.append(_user)
        return True


def get_database_client(database, user):
    if isinstance(database, str):
        database = Dict({'id': database})
    id = get_id(user)
    if id not in [user.id for user in _users]:
        raise Exception('user should be logged')

    database_auth = coll_database_authorization.find_one({'database.id': database.id, 'user.id': user.id},
                                                         {'_id': False})
    database = database_auth.database
    if database_auth is None:
        raise Exception('database no authorized')
    daemon = d1.anelys.daemon.find_one({'id': database.id}, {'_id': False})
    if daemon is None:
        raise Exception('database is not found')
    if daemon.system.lower() in ['mongodb', 'mongod', 'mongo']:
        config = Dict()
        if 'configuration' in database_auth:
            config = database_auth.configuration
            if 'connection' in config:
                conn = config.connection
                if 'uri' in conn:
                    return
        if 'location' in daemon and isinstance(daemon.location, Dict):
            if 'type' in daemon.location:
                pass
            elif 'id' in daemon.location and 'type' not in daemon.location:
                from dianna.local import get_host
                host = get_host(daemon.location)
                if host is not None:
                    config.host = host
                else:
                    if 'endpoint' in daemon:
                        pass


get_database_driver = get_database_client
get_database_connection = get_database_client
