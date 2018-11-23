from sarah.acp_bson import Recipient, Client
from anelys import get_id_with_name
from datetime import datetime
from decimal import Decimal as D
import dictutils
from math import trunc
from sarah.handler import Pool_Handler
import re
from dict import Dict as dict, List as list
from copy import deepcopy
from utils import find_one
from katherine import d1, d6, pymysql
from itzamara.remote import get_items_factor_related
from isodate import datetime_isoformat


emitter_stamp = {'id': '/valentine'}
agent_valentine = Client(emitter_stamp, '/valentine')
agent_itzamara = Client(emitter_stamp, '/itzamara')


valentine_db = d1.get_database('valentine')

coll_physical_count = valentine_db.get_collection('physical_count')
coll_trans = valentine_db['transaction']
coll_transfer = valentine_db.get_collection('transfer')
coll_transfer_order = valentine_db.get_collection('transfer_order')
coll_update_inventory = valentine_db['update_inventory']
coll_storage = valentine_db.get_collection('storage')
coll_vars = valentine_db.vars

r = coll_vars.find_one({'key': 'valentine/default_storage/id'}, {'_id': False, 'value': True})

if r is None:
    r = dict({'value': '42-3'})

default_storage = coll_storage.find_one({'id': r.value})


d6.ping(True)
d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
d6_cursor.execute('select * from valentine.balance as a where datetime = (select max(datetime) from valentine.balance '
                  'as b where a.storage_id = b.storage_id and a.item_sku = b.item_sku) ')
balances = [dict(b) for b in d6_cursor]

d6_cursor.close()


def convert_item_demand_columns_to_doc(item_demand):
    item_demand_doc = dict()
    if ('item_sku' in item_demand and item_demand['item_sku'] is not None) or\
            ('item_description' in item_demand and item_demand['item_description'] is not None):
        item_demand_doc['item'] = dict()
        if 'item_sku' in item_demand and item_demand['item_sku'] is not None:
            item_demand_doc['item']['sku'] = item_demand['item_sku']
        if 'item_description' in item_demand and item_demand['item_description'] is not None:
            item_demand_doc['item']['description'] = item_demand['item_description']
    if ('storage_id' in item_demand and item_demand['storage_id'] is not None) or \
            ('storage_type' in item_demand and item_demand['storage_type'] is not None):
        item_demand_doc['storage'] = dict()
        if 'storage_id' in item_demand and item_demand['storage_id'] is not None:
            item_demand_doc['storage']['id'] = item_demand['storage_id']
        if 'storage_type' in item_demand and item_demand['storage_type'] is not None:
            item_demand_doc['storage']['type'] = item_demand['storage_type']
    if 'demand' in item_demand and item_demand['demand'] is not None:
        item_demand_doc['demand'] = item_demand['demand']
    if 'period' in item_demand and item_demand['period'] is not None:
        item_demand_doc['period'] = item_demand['period']
    return item_demand_doc


def convert_item_demand_doc_to_columns(item_demand):
    item_demand_columns = dict()
    if 'item' in item_demand:
        item = item_demand['item']
        if 'sku' in item:
            item_demand_columns['item_sku'] = item['sku']
        else:
            item_demand_columns['item_sku'] = None
        if 'description' in item:
            item_demand_columns['item_description'] = item['description']
        else:
            item_demand_columns['item_description'] = None
    else:
        item_demand_columns['item_sku'] = None
        item_demand_columns['item_description'] = None
    if 'storage' in item_demand:
        storage = item_demand['storage']
        if 'id' in storage:
            item_demand_columns['storage_id'] = storage['id']
        else:
            item_demand_columns['storage_id'] = None
        if 'type' in storage:
            item_demand_columns['storage_type'] = storage['type']
        else:
            item_demand_columns['storage_type'] = None
    else:
        item_demand_columns['storage_id'] = None
        item_demand_columns['storage_type'] = None
    if 'demand' in item_demand:
        item_demand_columns['demand'] = item_demand['demand']
    else:
        item_demand_columns['demand'] = None
    if 'period' in item_demand:
        item_demand_columns['period'] = item_demand['period']
    else:
        item_demand_columns['period'] = None
    return item_demand_columns


def get_inventory_by_sku(sku, storage_id):
    if storage_id is None:
        storage_id = default_storage.id
    d6.ping(True)
    cursor = d6.cursor()
    inventory = D()
    balance = find_one(lambda x: x.item_sku == sku and x.storage_id == storage_id, balances)
    if balance is not None:
        inventory += balance.quanty
        if storage_id == default_storage.id:
            cursor.execute('SELECT CAST(IFNULL(SUM(quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.transaction WHERE datetime > %s and item_sku = %s AND '
                           '(storage_id IS NULL OR storage_id = %s) AND quanty IS NOT NULL;',
                           (balance.datetime, sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
            cursor.execute('SELECT CAST(IFNULL(SUM(split.quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.split INNER JOIN valentine.transaction AS tx '
                           'ON tx.id = split.transaction_id '
                           'WHERE tx.datetime > %s AND tx.item_sku = %s AND (split.storage_id IS NULL '
                           'OR split.storage_id = %s) AND tx.quanty IS NULL and split.quanty IS NOT NULL;',
                           (balance.datetime, sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
        else:
            cursor.execute('SELECT CAST(IFNULL(SUM(quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.`transaction` '
                           'WHERE datetime > %s and item_sku = %s AND storage_id = %s AND quanty IS NOT NULL;',
                           (balance.datetime, sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
            cursor.execute('SELECT CAST(IFNULL(SUM(split.quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.split INNER JOIN valentine.transaction AS tx '
                           'ON tx.id = split.transaction_id '
                           'WHERE tx.datetime > %s and tx.item_sku = %s AND split.storage_id = %s '
                           'AND tx.quanty IS NULL AND split.quanty IS NOT NULL;',
                           (balance.datetime, sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
    else:
        if storage_id == default_storage.id:
            cursor.execute('SELECT CAST(IFNULL(SUM(quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.transaction WHERE item_sku = %s AND (storage_id IS NULL OR '
                           'storage_id = %s) AND quanty IS NOT NULL;',
                           (sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
            cursor.execute('SELECT CAST(IFNULL(SUM(split.quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.split INNER JOIN valentine.transaction AS tx '
                           'ON tx.id = split.transaction_id '
                           'WHERE tx.item_sku = %s AND (split.storage_id IS NULL OR '
                           'split.storage_id = %s) AND tx.quanty IS NULL and split.quanty IS NOT NULL;',
                           (sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
        else:
            cursor.execute('SELECT CAST(IFNULL(SUM(quanty), 0) AS DECIMAL(15,3)) FROM valentine.`transaction` '
                           'WHERE item_sku = %s AND storage_id = %s AND quanty IS NOT NULL;',
                           (sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
            cursor.execute('SELECT CAST(IFNULL(SUM(split.quanty), 0) AS DECIMAL(15,3)) '
                           'FROM valentine.split INNER JOIN valentine.transaction AS tx '
                           'ON tx.id = split.transaction_id '
                           'WHERE tx.item_sku = %s AND split.storage_id = %s AND tx.quanty IS NULL '
                           'AND split.quanty IS NOT NULL;',
                           (sku, storage_id))
            quanty, = cursor.fetchone()
            inventory += quanty
    cursor.close()
    return inventory


def get_item_inventory(inventoring, storage):
    quantylowest = None
    factorlowest = None
    lowestcommon = None
    for itemrelated in inventoring.items_related:
        if itemrelated.factor_type == 'lowest_common':
            quantylowest = get_inventory_by_sku(itemrelated.sku, storage.id)
            factorlowest = itemrelated.factor
            lowestcommon = itemrelated
            break
    quanty = get_inventory_by_sku(inventoring.sku, storage.id)
    for itemrelated in inventoring.items_related:
        quanty_related = get_inventory_by_sku(itemrelated.sku, storage.id)
        if itemrelated.factor_type == 'up':
            quanty += quanty_related * itemrelated.factor
        elif itemrelated.factor_type in ['down']:
            quanty += quanty_related / itemrelated.factor
        elif itemrelated.factor_type == 'lowest':
            quantylowest += quanty_related * itemrelated.factor
    if quantylowest is None:
        return {'sku': inventoring.sku, 'description': inventoring.description, 'quanty': quanty}
    else:
        total_quantylowest = quantylowest + (quanty * factorlowest)
        quanty = trunc(total_quantylowest / factorlowest)
        quantylowest = total_quantylowest % factorlowest
        inventory = {'sku': inventoring.sku, 'description': inventoring.description, 'quanty': quanty}
        if quantylowest != D():
            itemfraction = {'sku': lowestcommon.sku, 'description': lowestcommon.description,
                            'factor': factorlowest, 'quanty': quantylowest}
            inventory.fraction = itemfraction
        return inventory




def split_doc_to_columns(split_doc, trans_doc):
    columns = dict()
    if 'id' in trans_doc:
        columns['transaction_id'] = trans_doc['id']
    else:
        columns['transaction_id'] = None
    if 'storage' in split_doc:
        if 'id' in split_doc['storage']:
            columns['storage_id'] = split_doc['storage']['id']
        else:
            columns['storage_id'] = None
        if 'type' in split_doc['storage']:
            columns['storage_type'] = split_doc['storage']['type']
        else:
            columns['storage_type'] = None
    else:
        columns['storage_id'] = None
        columns['storage_type'] = None
    if 'quanty' in split_doc:
        columns['quanty'] = split_doc['quanty']
    else:
        columns['quanty'] = None
    return columns


def trans_doc_to_columns(trans_doc):
    columns = dict()
    if 'id' in trans_doc:
        columns['id'] = trans_doc['id']
    else:
        columns['id'] = None
    if 'type' in trans_doc:
        columns['type'] = trans_doc['type']
    else:
        columns['type'] = None
    if 'datetime' in trans_doc:
        columns['datetime'] = trans_doc['datetime']
    else:
        columns['datetime'] = None
    if 'origen' in trans_doc:
        if 'id' in trans_doc['origen']:
            columns['origen_id'] = trans_doc['origen']['id']
        else:
            columns['origen_id'] = None
        if 'type' in trans_doc:
            columns['origen_type'] = trans_doc['origen']['type']
        else:
            columns['origen_type'] = None
    else:
        columns['origen_id'] = None
        columns['origen_type'] = None
    if 'storage' in trans_doc:
        if 'id' in trans_doc['storage']:
            columns['storage_id'] = trans_doc['storage']['id']
        else:
            columns['storage_id'] = None
        if 'type' in trans_doc['storage']:
            columns['storage_type'] = trans_doc['storage']['type']
        else:
            columns['storage_type'] = None
    else:
        columns['storage_id'] = None
        columns['storage_type'] = None
    if 'quanty' in trans_doc:
        columns['quanty'] = trans_doc['quanty']
    else:
        columns['quanty'] = None
    if 'item' in trans_doc:
        if 'sku' in trans_doc['item']:
            columns['item_sku'] = trans_doc['item']['sku']
        else:
            columns['item_sku'] = None
    else:
        columns['item_sku'] = None
    return columns


def persist_trans(trans):
    if 'type' not in trans:
        trans['type'] = 'valentine/transaction'
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('INSERT valentine.`transaction` (datetime, item_sku, storage_id, quanty, origen_id, '
                      'origen_type) VALUES (%(datetime)s, %(item_sku)s, %(storage_id)s, %(quanty)s, %(origen_id)s, '
                      '%(origen_type)s);', trans_doc_to_columns(trans))
    d6_cursor.close()
    dictutils.dec_to_float(trans)
    coll_trans.insert(trans)
    if '_id' in trans:
        del trans._id
    dictutils.float_to_dec(trans)


def update_inventory_item(item, storage_id=None, datetime_=None, update_inventory=None):
    if datetime_ is None:
        datetime_ = datetime_isoformat(datetime_.now())
    elif isinstance(datetime_, datetime):
        datetime_ = datetime_isoformat(datetime_)
    trans = dict()
    trans.datetime = datetime_
    trans.item = {'sku': item.sku}
    trans.storage = {'id': storage_id}
    inventory_existing = get_inventory_by_sku(item.sku, storage_id)
    if 'inventory_update' in item:
        trans.quanty = item.inventory_update - inventory_existing
    else:
        trans.quanty = - inventory_existing
    trans.origen = {'id': update_inventory.id, 'type': 'valentine/update_inventory'}
    if trans.quanty != D():
        persist_trans(trans)
        return trans


def handle_action_valentine_create_item_demand(msg):
    stmt = 'insert valentine.item_demand (item_sku, item_description, period, demand, storage_id, storage_type) ' \
           'VALUES (%(item_sku)s, %(item_description)s, %(period)s, %(demand)s, %(storage_id)s, %(storage_type)s) ' \
           'ON DUPLICATE KEY UPDATE period=values(period), demand=values(demand);'
    convert = convert_item_demand_doc_to_columns
    item_demand = msg.item_demand
    if 'storage' in item_demand:
        storage = item_demand.storage
    elif 'storage' in msg:
        storage = msg.storage
        item_demand.storage = storage
    elif default_storage is not None:
        storage = deepcopy(default_storage)
        item_demand.storage = storage
    else:
        storage = None
    for k in list(storage.keys()):
        if k not in ['id', 'type']:
            del storage[k]
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute(stmt, convert(item_demand))
    d6_cursor.close()


def handle_action_valentine_create_physical_count(msg):
    pc = msg.physical_count
    if 'type' not in pc:
        pc.type = 'valentine/physical_count'

    if 'id' not in pc:
        pc.id = get_id_with_name(pc.type)
    inventory = deepcopy(pc.count)
    for item in inventory:
        item.inventory_update = item.count
        del item.count
    msg = dict({'storage': pc.storage, 'inventory': inventory, 'physical_inventory': {'id': pc.id, 'type': pc.type}})
    answer = handle_action_valentine_update_inventory(msg)
    upd_inv = answer.update_inventory
    pc.update_inventory = {'id': upd_inv.id, 'type': upd_inv.type}
    dictutils.dec_to_float(pc)
    d1.valentine.physical_count.insert_one(pc)
    if '_id' in pc:
        del pc._id
    dictutils.float_to_dec(pc)
    return {'physical_count': pc}


def handle_action_valentine_create_transfer(msg):
    transfer = msg['transfer']
    if 'type' not in transfer:
        transfer['type'] = 'valentine/transfer'
    if 'id' not in transfer:
        transfer['id'] = get_id_with_name(transfer['type'])

    if 'datetime' not in transfer:
        transfer['datetime'] = datetime_isoformat(datetime.now())
    from_ = transfer['from']
    to = transfer['to']

    for k in list(from_.keys()):
        if k not in ['type', 'id', 'name', 'address']:
            del from_[k]

    for k in list(to.keys()):
        if k not in ['type', 'id', 'name', 'address']:
            del to[k]

    trans = {'origen': {'id': transfer['id'], 'type': transfer['type']},
             'storage': {'id': from_['id'], 'type': from_['type']}, 'datetime': transfer['datetime']}

    for item in transfer['items']:
        trans['item'] = {'sku': item['sku']}
        trans['quanty'] = - item['quanty']
        persist_trans(trans)

    trans['storage'] = {'id': to['id'], 'type': to['type']}
    for item in transfer['items']:
        trans['item'] = {'sku': item['sku']}
        trans['quanty'] = item['quanty']
        persist_trans(trans)

    dictutils.dec_to_float(transfer)
    coll_transfer.insert(transfer)


def handle_action_valentine_create_transfer_order(msg):
    transfer_order = msg.datetime
    if 'type' not in transfer_order:
        transfer_order.type = 'valentine/transfer_order'
    if transfer_order.type != 'valentine/transfer_order':
        raise Exception('no se puede crear una ordern de traslado de un tipo distinto a valentine/transfer_order')
    if 'id' not in transfer_order:
        transfer_order.id = get_id_with_name(transfer_order.type)
    if 'datetime' not in transfer_order and 'datetime' in msg:
        transfer_order.datetime = msg.datetime
    else:
        transfer_order.datetime = datetime_isoformat(datetime.now())
    dictutils.dec_to_float(transfer_order)
    coll_transfer_order.insert_one(transfer_order)
    del transfer_order._id
    return {'transfer_order': transfer_order}


def handle_action_valentine_update_inventory(msg):
    inventory = msg.inventory
    storage_id = None
    if 'storage' in msg and 'id' in msg.storage:
        storage_id = msg.storage.id
    with_their_related = False
    if 'with_their_related' in msg:
        with_their_related = msg.with_their_related
    upd_inv = dict()
    upd_inv.type = 'valentine/update_inventory'
    upd_inv.id = get_id_with_name(upd_inv.type)
    upd_inv.datetime = datetime_isoformat(datetime.now())
    if 'physical_count' in msg:
        upd_inv.physical_count = {'id': msg.physical_count.id, 'type': msg.physical_count.type}
    txs = list()
    for item in inventory:
        if with_their_related and 'items_related' not in item:
            item = get_items_related_factor(item)
        trans = update_inventory_item(item, storage_id, upd_inv.datetime, upd_inv)
        if trans is not None:
            txs.append(trans)
        if 'items_related' in item:
            for item_related in item.items_related:
                trans = update_inventory_item(item_related, upd_inv.datetime, upd_inv)
                if trans is not None:
                    txs.append(trans)
    upd_inv.transactions = txs
    dictutils.dec_to_float(upd_inv)
    coll_update_inventory.insert(upd_inv)
    del upd_inv._id
    return dict({'update_inventory': upd_inv})


def handle_action_valentine_make_movement(msg):
    is_mov_out = False
    if 'mov_type' in msg and msg.mov_type in ['out', 'exit']:
        is_mov_out = True
    if 'storage' in msg and isinstance(msg.storage, dict) and 'id' in msg.storage:
        storage = msg.storage
    else:
        storage = default_storage
    if 'mov_datetime' in msg:
        mov_datetime = msg.mov_datetime
    else:
        mov_datetime = datetime_isoformat(datetime.now())
    if 'origen' in msg:
        origen = msg.origen
        if 'id' not in origen:
            origen.id = None
    else:
        origen = {'id': None}
    trans = dict({'type': 'valentine/transaction', 'datetime': mov_datetime, 'storage': storage, 'origen': origen})
    for item in msg['items']:
        trans.item = {'sku': item.sku, 'description': item.description}
        if is_mov_out:
            trans.quanty = -item.quanty
        else:
            trans.quanty = item.quanty
        persist_trans(trans)


def handle_action_valentine_create_transaction(msg):
    return handle_action_valentine_make_movement(msg)


def handle_action_valentine_set_inventory(msg):
    if 'storage' in msg:
        storage = msg.storage
    else:
        storage = default_storage
    storage_id = storage.id

    def __help(it):
        trans = {'item': {'sku': it.sku, 'description': it.description}, 'storage': storage, 'datetime': dt}
        if 'inventory' in it:
            trans.quanty = it.inventory - it.c_inventory
        else:
            trans.quanty = -it.c_inventory
        persist_trans(trans)

    if 'item' in msg:
        item = msg.item
        if 'items_related' not in item:
            item = get_items_related_factor(item)
        for itemrelated in item.items_related:
            itemrelated.c_inventory = get_inventory_by_sku(itemrelated.sku, storage_id)
        item.c_inventory = get_inventory_by_sku(item.sku, storage_id)
        if 'datetime' in msg:
            dt = msg.datetime
        else:
            dt = datetime_isoformat(datetime.now())

        __help(item)

        for itemrelated in item.items_related:
            __help(itemrelated)
    elif 'items' in msg:
        pass


def handle_find_valentine_transfer(msg):
    l_filt = dict()
    result = [doc for doc in coll_transfer.find(l_filt, {'_id': False})]
    return {'result': result}


def handle_find_valentine_transfer_order(msg):
    l_filt = dict()
    result = [doc for doc in coll_transfer_order.find(l_filt, {'_id': False})]
    return {'result': result}


def handle_find_valentine_storage(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            l_filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.I)
    result = list(coll_storage.find(l_filt, {'_id': False}))
    return {'result': result}


def handle_find_one_valentine_storage(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filt['id'] = v1
    return {'result': coll_storage.find_one(l_filt, {'_id': False})}


def handle_find_one_valentine_transfer(msg):
    l_filt = dict()
    return {'result': coll_transfer.find_one(l_filt, {'_id': False})}


def handle_find_one_valentine_transfer_order(msg):
    l_filt = dict()
    return {'result': coll_transfer_order.find_one(l_filt, {'_id': False})}


def handle_get_valentine_get_item_demand(msg):
    convert_to_doc = convert_item_demand_columns_to_doc
    if 'storage' in msg:
        storage = msg['storage']
    else:
        storage = deepcopy(default_storage)
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    d6_cursor.execute('SELECT item_sku, item_description, storage_id, storage_type, period, demand FROM '
                      'valentine.item_demand WHERE storage_id = %s;', (storage.id,))
    result = [convert_to_doc(item_demand) for item_demand in d6_cursor]
    d6_cursor.close()
    return {'result': result}

def get_inventory_absolut(storage, item):
    def get_inv_by_sku(__sku):
        return get_inventory_by_sku(item.sku, storage.id)

    inventory_absolut = get_inv_by_sku(item.sku)

    if 'items_related' in item:
        inventory_factorized = D()
        for itemrelated in item.items_related:
            if itemrelated.factor_type == 'lowest_common':
                inventory_factorized += get_inv_by_sku(itemrelated.sku) / itemrelated.factor
                lowestcommonfactor = itemrelated.factor
                break
        else:
            lowestcommonfactor = None
        for itemrelated in item.items_related:
            if itemrelated.factor_type == 'up':
                inventory_factorized += get_inv_by_sku(itemrelated.sku) * itemrelated.factor
            elif itemrelated.factor_type == 'down':
                inventory_factorized += get_inv_by_sku(itemrelated.sku) / itemrelated.factor
            elif itemrelated.factor_type == 'lowest':
                inventory_factorized += (get_inv_by_sku(itemrelated.sku) / lowestcommonfactor) * itemrelated.factor
        inventory_absolut += inventory_factorized
    return inventory_absolut


def handle_get_valentine_inventory_absolut(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()

    if 'storage' in msg or 'store' in msg:
        if 'storage' in msg:
            storage = msg.storage
        elif 'store' in msg:
            storage = msg.store
        else:
            storage = default_storage

        had = True

        if 'item' in msg:
            item = msg.item
            if 'items_related' not in item:
                had = False
                item = get_items_factor_related(item)
            item.inventory_absolut = get_inventory_absolut(storage, item)
            if not had and 'items_related' in item:
                del item.items_related
            reply = dict({'item': item})
        elif 'items' in msg:
            items = msg['items']
            for item in items:
                if 'items_related' not in item:
                    had = False
                    items = get_items_factor_related(items)
                    break

            for item in items:
                item.inventory_absolut = get_inventory_absolut(item)
                if not had and 'items_related' in item: del item.items_related
            reply = dict({'items': items})
        else:
            reply = dict()

    elif 'storages' in msg:
        storages = msg.storages
        if 'item' in msg:
            item = msg.item
            if 'items_related' not in item:
                had = False
                item = get_items_factor_related(item)
            else:
                had = True
            item.inventory_absolut = {}
            for storage in storages:
                item.inventory_absolut[storage.id] = get_inventory_absolut(storage, item)

            if not had:
                del item.items_related
            reply = dict({'item': item})
        elif 'items' in msg:
            items = msg.items
            for item in items:
                if 'items_related' not in item:
                    items = get_items_factor_related(items)
                    had = False
                    break
            else:
                had = True

            for item in items:
                item.inventory_absolut = {}
                for storage in storages:
                    item.inventory_absolut[storage.id] = get_inventory_absolut(storage, item)
                if not had:
                    del item.items_related
            reply = dict({'items': items})
        else:
            reply = dict()
    else:
        reply = dict()

    def put_projection_updated(item):
        r = d6_cursor.execute('select datetime from valentine.transaction '
                              'where storage_id = %s and item_sku = %s and origen_type = %s '
                              'order by datetime desc limit 1;', (storage.id, item.sku, 'valentine/update_inventory'))
        if r == 1:
            updated, = d6_cursor.fetchone()
            item.updated = datetime_isoformat(updated)

    if 'projection' in msg:
        projection = msg.projection
        if 'updated' in projection and projection.updated and 'storages' not in msg:
            if 'item' in reply:
                put_projection_updated(reply.item)
            elif 'items' in reply:
                for item in reply['items']:
                    put_projection_updated(item)
        if 'inventory' in projection and projection.inventory:
            if 'item' in reply:
                reply.item.inventory = reply.item.inventory_absolut
            elif 'items' in reply:
                for item in reply['items']:
                    item.inventory = item.inventory_absolut
        if 'inventory_absolut' in projection and not projection.inventory_absolut:
            if 'item' in reply:
                del reply.item.inventory_absolut
            elif 'items' in reply:
                for item in reply['items']:
                    del item.inventory_absolut

    d6_cursor.close()
    return reply


def handle_get_valentine_inventory_by_sku(msg):
    if 'storage' in msg:
        storage_id = msg.storage.id
    else:
        storage_id = default_storage.id
    reply = None

    def __help_items_related(_item):
        if 'items_related' in _item:
            for itemrelated in _item.items_related:
                itemrelated.inventory = get_inventory_by_sku(itemrelated.sku, storage_id)
        elif 'itemsrelated' in _item.itemsrelated:
            for itemrelated in _item:
                itemrelated.inventory = get_inventory_by_sku(itemrelated.sku, storage_id)
    if 'item' in msg:
        item = msg.item
        item.inventory = get_inventory_by_sku(item.sku, storage_id)
        __help_items_related(item)
        reply = {'item': item}
    elif 'items' in msg:
        items = msg['items']
        for item in items:
            item.inventory = get_inventory_by_sku(item.sku, storage_id)
            __help_items_related(item)
        reply = {'items': items}
    return reply


def handle_get_valentine_transfer_order_pending(msg):
    l_filt = {'transfer': {'$exists': False}}
    result = [doc for doc in coll_transfer_order.find(l_filt, {'_id': False})]
    return {'result': result}


def handle_inform_valentine_inventory(msg):
    query = msg.query
    if 'storage' in query:
        storage = query.storage
        if 'id' not in storage:
            storage.id = None
    else:
        storage = {'id': None}
    inventoring = query.inventoring
    if isinstance(inventoring, dict) and ('type' not in inventoring or inventoring.type == 'itzamara/item'):
        # si estamos inventariando en la consulta un solo articulo
        if 'items_related' not in inventoring:
            inventoring = get_items_related_factor(inventoring)
        inventory = get_item_inventory(inventoring, storage)
    else:
        # entonces es algun tipo de lista
        inventoringlist = None
        if isinstance(inventoring, dict) and 'type' in inventoring and inventoring.type == 'itzamara/item_list':
            inventoringlist = inventoring['items']
        elif isinstance(inventoring, list):
            inventoringlist = inventoring
        for inventoring in inventoringlist:
            if 'items_related' in inventoring:
                break
        else:
            inventoringlist = get_items_related_factor(inventoringlist)
        inventory = list()
        for inventoring in inventoringlist:
            inventory.append(get_item_inventory(inventoring, storage))
    return {'inform': {'inventory': inventory}}


rr = Pool_Handler()
rr['type_message=action.action=valentine/create_item_demand'] = handle_action_valentine_create_item_demand
rr['type_message=action.action=valentine/create_physical_count'] = handle_action_valentine_create_physical_count
rr['type_message=action.action=valentine/create_transaction'] = handle_action_valentine_create_transaction
rr['type_message=action.action=valentine/create_transfer'] = handle_action_valentine_create_transfer
rr['type_message=action.action=valentine/edit_item_demand'] = handle_action_valentine_create_item_demand
rr['type_message=action.action=valentine/make_movement'] = handle_action_valentine_make_movement
rr['type_message=action.action=valentine/make_physical_count'] = handle_action_valentine_create_physical_count
rr['type_message=action.action=valentine/update_inventory'] = handle_action_valentine_update_inventory
rr['type_message=action.action=valentine/update_item_demand'] = handle_action_valentine_create_item_demand
rr.reg('type_message=action.action=valentine/set_inventory', handle_action_valentine_set_inventory)
rr.reg('type_message=find.type=valentine/storage', handle_find_valentine_storage)
rr.reg('type_message=find_one.type=valentine/storage', handle_find_one_valentine_storage)
rr.reg('type_message=request.request_type=inform.inform=valentine/inventory', handle_inform_valentine_inventory)
rr.reg('type_message=request.request_type=get.get=valentine/get_item_demand', handle_get_valentine_get_item_demand)
rr.reg('type_message=request.request_type=get.get=valentine/inventory_by_sku', handle_get_valentine_inventory_by_sku)
rr['type_message=request.request_type=get.get=valentine/inventory_absolut'] = handle_get_valentine_inventory_absolut

if __name__ == '__main__' and True:
    print("I'm valentine")
    recipient = Recipient()
    recipient.prepare('/valentine', rr)
    recipient.begin_receive_forever()
