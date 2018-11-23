from katherine import pymysql, d1, d5, d6
from sarah.acp_bson import Recipient, Pool_Handler
import re
from dict import Dict as dict, List as list
from itzamara import key_to_sort_item
from utils import isnumeric
from isodate import datetime_isoformat


db_itzamara = d1.itzamara
coll_item_list = db_itzamara.get_collection('item_list')


def item_column_to_doc(column):
    doc = dict()
    if column['sku'] is not None:
        doc.sku = column['sku']
    if column['description'] is not None:
        doc.description = column['description']
    if column['unit_measure'] is not None:
        doc.unit_measure = column['unit_measure']
    if column['mass_n'] is not None and column['mass_unit'] is not None:
        doc.mass = {'n': column['mass_n'], 'unit': column['mass_unit']}
    if column['modified'] is not None:
        doc.modified = datetime_isoformat(column['modified'])
    if column['created'] is not None:
        doc.created = datetime_isoformat(column['created'])
    if column['pack'] is not None:
        doc.pack = True if column['pack'] else False
    if column['lifetime'] is not None:
        doc.lifetime = column['lifetime']
    return doc


def item_doc_to_column(doc):
    column = dict()
    if 'sku' in doc:
        column.sku = doc.sku
    else:
        column.sku = None

    if 'description' in doc:
        column.description = doc.description
    else:
        column.description = None

    if 'unit_measure' in doc:
        column.unit_measure = doc.unit_measure
    else:
        column.unit_measure = None

    if 'mass' in doc:
        mass = doc
        if 'n' in mass:
            column.mass_n = mass.n
        else:
            column.mass_n = None

        if 'unit' in mass:
            column.mass_unit = mass.unit
        else:
            column.mass_unit = None
    else:
        column.mass_n = None
        column.mas_unit = None

    if 'modified' in doc:
        column.modified = doc.modified
    else:
        column.modified = None

    if 'created' in doc:
        column.created = doc.created
    else:
        column.created = None

    if 'lifetime' in doc:
        column.lifetime = doc.lifetime
    else:
        column.lifetime = None
    return column


item_d1_to_d6 = item_doc_to_column
item_d6_to_d1 = item_column_to_doc


def allocate_item_sku(prefix=None):
    d6.ping(True)
    d6_cursor = d6.cursor()

    if prefix is not None:
        r = d6_cursor.execute('select serie from itzamara.allocate_sku where prefix = %s limit 1;', (prefix, ))
        if r == 1:
            serie, = d6_cursor.fetchone()
            if isnumeric(prefix[-1]):
                sku = prefix + '-' + str(serie)
            else:
                sku = prefix + str(serie)
            d6_cursor.execute('update itzamara.allocate_sku set serie = serie + 1 where prefix = %s limit 1;', (prefix, ))
        else:
            if isnumeric(prefix[-1]):
                sku = prefix + '-1'
            else:
                sku = prefix + '1'
            d6_cursor.execute('insert itzamara.allocate_sku (prefix, serie) values (%s, 2);', (prefix, ))
    else:
        r = d6_cursor.execute('select serie from itzamara.allocate_sku where prefix is NULL limit 1;')
        if r == 1:
            serie, = d6_cursor.fetchone()
            sku = str(serie)
            d6_cursor.execute('update itzamara.allocate_sku set serie = serie +1 where prefix IS NULL limit 1;')
        else:
            sku = '1'
            d6_cursor.execute('insert itzamara.allocate_sku (prefix, serie) values (NULL, 2);')
    d6_cursor.close()
    return sku


def get_item_factor_related_v1(item):
    d6.ping(True)
    d6_cursor = d6.cursor()
    select_stmt = 'SELECT pack.sku, pack.description, pack_factor.factor FROM itzamara.pack AS pack_factor INNER ' \
                  'JOIN itzamara.item ON item.sku = pack_factor.item_sku INNER JOIN itzamara.item AS pack ON ' \
                  'pack.sku = pack_factor.pack_sku WHERE item.sku = %s;'
    curr_factor = 1
    sku_to_search = item.sku
    sku_reviewed = [item.sku]
    items_related = list()
    all_checked = False
    while not all_checked:
        # busqueda upside
        d6_cursor.execute(select_stmt, (sku_to_search,))
        for sku, description, factor in d6_cursor:
            if sku not in sku_reviewed:
                sku_reviewed.append(sku)
                items_related.append({'sku': sku,
                                      'description': description,
                                      'factor': curr_factor * factor,
                                      'factor_type': 'up',
                                      'checked_up': False,
                                      'checked_down': False})
        for item_related in items_related:
            if 'checked_up' in item_related and not item_related['checked_up']:
                sku_to_search = item_related['sku']
                curr_factor = item_related['factor']
                del item_related['checked_up']
                break
        else:
            all_checked = True
    lowest_common = None
    sku_to_search = item['sku']
    curr_factor = 1
    while True:
        select_stmt = 'SELECT item.sku, item.description, pack_factor.factor FROM itzamara.pack AS pack_factor ' \
                      'INNER JOIN itzamara.item ON item.sku = pack_factor.item_sku ' \
                      'INNER JOIN itzamara.item AS pack ON pack.sku = pack_factor.pack_sku ' \
                      'WHERE pack.sku = %s LIMIT 1;'
        d6_cursor.execute(select_stmt, (sku_to_search,))
        if d6_cursor.rowcount > 0:
            for sku, description, factor in d6_cursor:
                lowest_common = {'sku': sku,
                                 'description': description,
                                 'factor': curr_factor * factor}
                sku_to_search = sku
                curr_factor = curr_factor * factor
        else:
            break
    if lowest_common is not None:
        sku_reviewed.append(lowest_common['sku'])
        lowest_common['factor_type'] = 'lowest_common'
        lowest_common['checked_up'] = False
        items_related.append(lowest_common)
        all_checked = False
        curr_factor = 1
        sku_to_search = lowest_common['sku']
        while True:
            select_stmt = 'SELECT pack.sku, pack.description, pack_factor.factor ' \
                          'FROM itzamara.pack AS pack_factor ' \
                          'INNER JOIN itzamara.item ON item.sku = pack_factor.item_sku ' \
                          'INNER JOIN itzamara.item AS pack ON pack.sku = pack_factor.pack_sku WHERE item.sku = %s;'
            d6_cursor.execute(select_stmt, (sku_to_search,))
            for sku, description, factor in d6_cursor:
                if sku not in sku_reviewed:
                    sku_reviewed.append(sku)
                    items_related.append({'sku': sku,
                                          'description': description,
                                          "factor": curr_factor * factor,
                                          "factor_type": 'lowest',
                                          'checked_up': False})
            for item_related in items_related:
                if 'checked_up' in item_related and not item_related['checked_up']:
                    curr_factor = item_related['factor']
                    sku_to_search = item_related['sku']
                    del item_related['checked_up']
                    break
            else:
                break
    for item_related in items_related:
        if 'checked_down' in item_related:
            del item_related['checked_down']
        if 'checked_up' in item_related:
            del item_related['checkep_up']
    d6_cursor.close()
    return items_related


def handle_get_itzamara_items_factor_related(msg):
    if 'v' in msg and msg['v'] == 2:
        if 'items' in msg:
            items = msg['items']
            if isinstance(items, list):
                for item in items:
                    item['items_related'] = get_item_factor_related(item)
                return {'items': items}
        elif 'item' in msg:
            item = msg['item']
            item['items_related'] = get_item_factor_related(item)
            return {'item': item}
        elif 'query' in msg and 'items' in msg['query']:
            items = msg['query']['items']
            if isinstance(items, list):
                for item in items:
                    item['items_related'] = get_item_factor_related(item)
                return {'items': items}
        elif 'query' in msg and 'item' in msg['query']:
            item = msg['query']['item']
            item['items_related'] = get_item_factor_related(item)
            return {'item': item}
    else:
        if 'items' in msg:
            items = msg['items']
            if isinstance(items, list):
                for item in items:
                    item['items_related'] = get_item_factor_related_v1(item)
                return {'items': items}
        elif 'item' in msg:
            item = msg['item']
            item['items_related'] = get_item_factor_related_v1(item)
            return {'item': item}
        elif 'query' in msg and 'items' in msg['query']:
            items = msg['query']['items']
            if isinstance(items, list):
                for item in items:
                    item['items_related'] = get_item_factor_related_v1(item)
                return {'items': items}
        elif 'query' in msg and 'item' in msg['query']:
            item = msg['query']['item']
            item['items_related'] = get_item_factor_related_v1(item)
            return {'item': item}


def get_item_factor_related(item):
    d5_session = d5.session()
    item_origen = item
    items_related = list()
    skus_checked = [item_origen['sku']]

    lowest_common = None
    sku = item_origen['sku']
    factor = 1
    while True:
        result = d5_session.run('MATCH ({sku:{sku}})<-[pack:pack]-(item) RETURN item.sku as sku, item.description '
                                'as description, item.type as type, pack.quanty as quanty;', {'sku': sku})
        record = result.single()
        if record is None:
            break
        factor *= record['quanty']
        sku = record['sku']
        lowest_common = {'factor': factor, 'factor_type': 'lowest_common'}
        if record['sku'] is not None:
            lowest_common['sku'] = record['sku']
        if record['description'] is not None:
            lowest_common['description'] = record['description']
        if record['type'] is not None:
            lowest_common['type'] = record['type']
    if lowest_common is not None:
        items_related.append(lowest_common)
        skus_checked.append(lowest_common['sku'])
        sku = lowest_common['sku']
        factor = 1
        while True:
            result = d5_session.run('MATCH ({sku:{sku}})-[pack:pack]->(item_pack) RETURN item_pack.sku as pack_sku, '
                                    'item_pack.description as pack_description, item_pack.type as pack_type, '
                                    'pack.quanty as quanty;', {'sku': sku})
            for record in result:
                itemrelated = {'factor_type': 'lowest', 'checked_up': False, 'factor': factor * record['quanty']}
                if record['pack_sku'] is not None:
                    itemrelated['sku'] = record['pack_sku']
                if record['pack_description'] is not None:
                    itemrelated['description'] = record['pack_description']
                if record['pack_type'] is not None:
                    itemrelated['type'] = record['pack_type']
                if 'sku' in itemrelated and itemrelated['sku'] not in skus_checked:
                    skus_checked.append(itemrelated['sku'])
                    items_related.append(itemrelated)
            for itemrelated in items_related:
                if 'checked_up' in itemrelated:
                    del itemrelated['checked_up']
                    sku = itemrelated['sku']
                    factor = itemrelated['factor']
                    break
            else:
                break
        sku = item_origen['sku']
        factor = 1
        while True:
            result = d5_session.run('MATCH ({sku:{sku}})-[pack:pack]->(item_pack) RETURN item_pack.sku as pack_sku, '
                                    'item_pack.description as pack_description, item_pack.type as pack_type, '
                                    'pack.quanty as quanty;', {'sku': sku})
            for record in result:
                itemrelated = {'factor_type': 'up', 'checked_up': False, 'factor': factor * record['quanty']}
                if record['pack_sku'] is not None:
                    itemrelated['sku'] = record['pack_sku']
                if record['pack_description'] is not None:
                    itemrelated['description'] = record['pack_description']
                if record['pack_type'] is not None:
                    itemrelated['type'] = record['pack_type']
                if 'sku' in itemrelated and itemrelated['sku'] not in skus_checked:
                    skus_checked.append(itemrelated['sku'])
                    items_related.append(itemrelated)
            for itemrelated in items_related:
                if 'checked_up' in itemrelated:
                    del itemrelated['checked_up']
                    sku = itemrelated['sku']
                    factor = itemrelated['factor']
                    break
            else:
                break

    else:  # then item_origen already is lowest_common now I'll search up
        sku = item_origen['sku']
        factor = 1
        while True:
            result = d5_session.run('MATCH ({sku:{sku}})<-[pack:pack]-(item_pack) RETURN item_pack.sku as pack_sku, '
                                    'item_pack.description as pack_description, item_pack.type as pack_type, '
                                    'pack.quanty as quanty;', {'sku': sku})
            for record in result:
                itemrelated = {'factor_type': 'up', 'checked_up': False, 'factor': factor * record['quanty']}
                if record['pack_sku'] is not None:
                    itemrelated['sku'] = record['pack_sku']
                if record['pack_description'] is not None:
                    itemrelated['description'] = record['pack_description']
                if record['pack_type'] is not None:
                    itemrelated['type'] = record['pack_type']
                if 'sku' in itemrelated and itemrelated['sku'] not in skus_checked:
                    skus_checked.append(itemrelated['sku'])
                    items_related.append(itemrelated)
            for itemrelated in items_related:
                if 'checked_up' in itemrelated:
                    del itemrelated['checked_up']
                    sku = itemrelated['sku']
                    factor = itemrelated['factor']
                    break
            else:
                break
    d5_session.close()
    return items_related


def get_sku_related_to_code_ref(code_ref):
    d6.ping(True)
    d6_cursor = d6.cursor()
    r = d6_cursor.execute('select sku from itzamara.code_ref WHERE code_ref = %s and type = %s',
                          (code_ref, 'itzamara/code_ref'))
    if r == 1:
        sku, = d6_cursor.fetchone()
    else:
        r = d6_cursor.execute('SELECT sku FROM itzamara.code_ref where code_ref = %S and type in (%s, %s);',
                              (code_ref, 'itzamara/code', 'itzamara/bar_code_alias'))
        if r == 1:
            sku, = d6_cursor.fetchone()
        else:
            sku = None
    d6_cursor.close()
    return sku


def persist_item(item_doc=None, item_column=None):
    d6.ping(True)
    d6_cursor = d6.cursor()
    if item_doc is None and item_column is None:
        raise Exception('unless an item_doc or item_column should not be None')
    elif item_doc is not None and item_column is None:
        item_column = item_d1_to_d6(item_doc)
    elif item_doc is None and item_column is not None:
        item_doc = item_d6_to_d1(item_column)

    d6_cursor.execute('INSERT itzamara.item (sku, description, unit_measure, mass_n, mass_unit, lifetime) values '
                      '(%(sku)s, %(description)s, %(unit_measure)s, %(mass_n)s, %(mass_unit)s, %(lifetime)s) '
                      'ON DUPLICATE KEY description = %(description)s, unit_measure = %(unit_measure)s, '
                      'mass_n = %(mass_n)s, mass_unit = %(mass_unit)s, lifetime = %(lifetime)s;', item_column)
    d6_cursor.close()
    d1.itzamara.item.replace_one({'sku': item_doc.sku}, item_doc, True)


def handle_action_create_item(msg):
    d6.ping(True)
    d6_cursor = d6.cursor()
    item = msg.item

    if 'sku' not in item:
        if 'prefixs_sku' in msg:
            item.sku = allocate_item_sku(msg.prefixs_sku)
        else:
            item.sku = allocate_item_sku()
    else:
        r = d6_cursor.execute('select sku from itzamara.item where sku = %s limit 1;', (item.sku, ))
        if r == 1:
            raise Exception('cannot be created a item with a sku that already exists;')
    item_column = item_d1_to_d6(item)
    persist_item(item_doc=item, item_column=item_column)

    def reg_code_ref(item, code_ref):
        d6_cursor.execute('insert itzamara.code_ref (sku, code_ref, type) values (%s, %s, %s);',
                          (item.sku, code_ref.code_ref, code_ref.type))

    if 'code_ref' in msg:
        reg_code_ref(item, msg.code_ref)
    elif 'codes_ref' in msg:
        for code_ref in msg.codes_ref:
            reg_code_ref(item, code_ref)
    d6_cursor.close()
    return {'item': item}


def handle_action_edit_item(msg):
    pass


def handle_get_itzamara_item_related_to_code_ref(msg):
    sku = get_sku_related_to_code_ref(msg.code_ref)
    if sku is not None:
        d6.ping(True)
        d6_cursor = d6.cursor()
        r = d6_cursor.execute('SELECT description FROM itzamara.item WHERE sku = %s LIMIT 1;', (sku,))
        if r == 1:
            desc, = d6_cursor.fetchone()
            item = {'sku': sku, 'description': desc, 'type': 'itzamara/item'}
        else:
            item = None
        d6_cursor.close()
    else:
        item = None
    return {'result': item}


def handle_get_itzamara_item_sku_related_to_code_ref(msg):
    return {'result': get_sku_related_to_code_ref(msg.code_ref)}


def handle_get_itzamara_item_mass(msg):
    pass
    if 'query' in msg and 'item' in msg['query']:
        item = msg['query']['item']
    elif 'item' in msg:
        item = msg['item']
    else:
        raise Exception('msg should contains item')

    d6.ping(True)
    d6_cursor = d6.cursor()
    r = d6_cursor.execute('select mass_unit, mass_n from itzamara.item where sku = %s limit 1;',
                          (item['sku'],))
    if r == 1:
        mass_unit, mass_n = d6_cursor.fetchone()
        if mass_unit is not None and mass_n is not None:
            mass = {'n': mass_n, 'unit': mass_unit}
        else:
            mass = None
    else:
        mass = None
    d6_cursor.close()
    return {'mass': mass}


def handle_get_itzamara_units_mass(msg):
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    d6_cursor.execute('select name, symbol, multiple_gram from itzamara.unit_mass;')
    result = d6_cursor.fetchall()
    d6_cursor.close()
    return {'result': result}


def handle_find_itzamara_item(msg):
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    stmt = 'SELECT sku, description, unit_measure, mass_n, mass_unit, modified, created, lifetime, pack FROM itzamara.item'
    clausules = list()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'description':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            clausules.append('description LIKE \'%' + v2.replace(' ', '%').replace("'", "\\'") + '%\'')
    if len(clausules):
        stmt += ' WHERE ' + ' AND '.join(clausules)

    if 'limit' in msg and msg.limit:
        stmt += ' LIMIT ' + str(msg.limit)
        
    d6_cursor.execute(stmt)
    result = list([item_column_to_doc(item) for item in d6_cursor])
    d6_cursor.close()

    if 'query' in msg and 'store' in msg.query and 'id' in msg.query.store:
        store_id = msg.query.store.id

        d5_session = d5.session()
        rr = d5_session.run('MATCH (store{id:{store_id}}) '
                            'MATCH (item) where item.sku in {items_sku} and ((store)-[:not_sells]->(item)) '
                            'RETURN item.sku as sku;',
                            {'store_id': store_id, 'items_sku': [item.sku for item in result]})

        d5_session.close()
        result = list(filter(lambda x: x.sku not in [rc['sku'] for rc in rr], result))

    if 'sort' in msg and isinstance(msg.sort, bool) and msg.sort:
        result.sort(key=key_to_sort_item)
    return {'result': result}


def handle_find_itzamara_item_list(msg):
    lft = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            lft['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.I)
    return {'result': list(coll_item_list.find(lft, {'_id': False}))}


def handle_find_one_itzamara_item(msg):
    if 'multi' not in msg or not msg['multi']:
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('SELECT description FROM itzamara.item WHERE sku = %s LIMIT 1;', (msg.query.sku,))
        if d6_cursor.rowcount == 1:
            descr, = d6_cursor.fetchone()
            item = {'sku': msg.query.sku, 'description': descr, 'type': 'itzamara/item'}
        else:
            item = None
        d6_cursor.close()
        return {'result': item}
    else:
        d6.ping(True)
        d6_cursor = d6.ping()
        result = list()
        for sku in msg['sku']:
            d6_cursor.execute('SELECT description FROM itzamara.item WHERE sku = %s LIMIT 1;',
                              (sku, ))
            if d6_cursor.rowcount == 1:
                desc, = d6_cursor.fetchone()
                item = {'sku': sku, 'description': desc, 'type': 'itzamara/item'}
            else:
                item = None
            result.append(item)
        d6_cursor.close()
        return {'result': result}


def handle_find_one_itzamara_item_list(msg):
    lft = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                lft['id'] = v1
    return {'result': coll_item_list.find_one(lft, {'_id': False})}


def handle_get_itzamara_code_ref(msg):
    if 'item' in msg and 'sku' in msg['item']:
        item_sku = msg['item']['sku']
    elif 'query' in msg and 'item' in msg['query'] and 'sku' in msg['query']['item']:
        item_sku = msg['query']['item']['sku']
    else:
        raise Exception('request should contains an item\'s sku')

    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)

    d6_cursor.execute('SELECT code_ref, type FROM itzamara.code_ref WHERE sku = %s;', (item_sku,))
    codes_ref = list(d6_cursor)
    d6_cursor.close()
    return {'result': codes_ref}


def handle_question_itzamara_item_expires(msg):
    pass


read_msg = Pool_Handler()
rr = read_msg
rr['type_message=action.action=itzamara/create_item'] = handle_action_create_item
rr.reg('type_message=find.type=itzamara/item', handle_find_itzamara_item)
rr.reg('type_message=find.type=itzamara/item_list', handle_find_itzamara_item_list)
rr.reg('type_message=find_one.type=itzamara/item', handle_find_one_itzamara_item)
rr.reg('type_message=find_one.type=itzamara/item_list', handle_find_one_itzamara_item_list)
rr.reg('type_message=request.request_type=get.get=itzamara/code_ref', handle_get_itzamara_code_ref)
rr.reg('type_message=request.request_type=get.get=itzamara/get_item_mass', handle_get_itzamara_item_mass)
rr.reg('type_message=request.request_type=get.get=itzamara/get_items_factor_related',
       handle_get_itzamara_items_factor_related)
rr.reg('type_message=request.request_type=get.get=itzamara/items_factor_related',
       handle_get_itzamara_items_factor_related)
rr.reg('type_message=request.request_type=get.get=itzamara/item_related_to_code_ref',
       handle_get_itzamara_item_related_to_code_ref)
rr.reg('type_message=request.request_type=get.get=itzamara/units_mass', handle_get_itzamara_units_mass)
rr['type_message=question.question=itzamara/item_expires'] = handle_question_itzamara_item_expires


from itzamarad import actions
actions.map_functions(rr)

if __name__ == '__main__':
    print("I'm itzamara")
    recipient = Recipient()
    recipient.prepare('/itzamara', read_msg)
    recipient.begin_receive_forever()
