from sarah.acp_bson import Recipient, Pool_Handler
from sarah import dictutils
from anelys import get_id_with_name
from datetime import datetime
from isodate import date_isoformat, datetime_isoformat, parse_datetime
from katherine import d1, d5, d6
from dict import Dict as dict, List as list
import dictutils

db_kristine = d1.kristine
coll_check_policy = db_kristine.get_collection('check_policy')
coll_transaction = db_kristine.get_collection('transaction')
coll_split = db_kristine.get_collection('split')
coll_vars = db_kristine.get_collection('vars')


def split_dict_to_columns(split, tx):
    columns = dict()
    columns['id'] = split.id if 'id' in split else None
    columns['tx_id'] = tx['id'] if 'id' in tx else None
    columns['datetime'] = split['datetime'] if 'datetime' in split else tx['datetime'] if 'datetime' in tx else None
    columns['date'] = split['date'] if 'date' in split else tx['date'] if 'date' in tx else None
    columns['num'] = split['num'] if 'num' in split else tx['num'] if 'num' in tx else None
    columns['description'] = split['description'] if 'description' in split else tx['description'] if 'description' in tx else None
    columns['account_id'] = split['account']['id'] if 'account' in split and 'id' in split['account'] else None
    columns['value'] = split['value'] if 'value' in split else None
    return columns


def tx_dict_to_columns(tx):
    columns = dict()
    columns['id'] = tx['id'] if 'id' in tx else None
    columns['type'] = tx['type'] if 'type' in tx else None
    columns['datetime'] = tx['datetime'] if 'datetime' in tx else None
    columns['date'] = tx['date'] if 'date' in tx else None
    columns['num'] = tx['num'] if 'num' in tx else None
    columns['description'] = tx['description'] if 'description' in tx else None
    return columns


def get_split_next_num(account):
    d6.ping(True)
    cursor = d6.cursor()
    r = cursor.execute('select num_next from kristine.account where id = %s limit 1;', (account.id, ))
    if r == 1:
        num, = cursor.fetchone()
        cursor.execute('update kristine.account set num_next = num_next + 1 where id = %s;', (account.id, ))
    else:
        num = 1
        cursor.execute('insert kristine.account (id, num_next) values (%s , 2);', (account.id, ))

    cursor.close()
    return num


def get_tx_next_num():
    k = 'kristine/transaction/next_num'
    vars = coll_vars.find_one({'key': k})
    if vars is not None:
        num = vars.value
        coll_vars.update_one({'key': k}, {'$inc': {'value': 1}})
    else:
        coll_vars.insert_one({'key': k, 'value': 2})
        num = 1
    return num


def remove_transaction(tx, with_split=False):
    if isinstance(tx, str):
        tx = dict({'id': tx})
    if 'id' not in tx or tx.id is None:
        raise Exception('should inclucde tx.id')
    d5_session = d5.session()
    rr = d5_session.run('match (n{id:{id}}) detach delete n;', {'id': tx.id})
    rr.single()
    d5_session.close()
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('delete from kristine.transaction where id = %s;', (tx.id,))
    tx = coll_transaction.find_one({'id': tx.id}, {'_id': False})

    coll_transaction.remove({'id': tx.id})
    if with_split:
        if 'splits' in tx:
            for split in [split for split in tx.splits if 'id' in split]:
                remove_split(split)
    else:
        coll_split.update_many({'transaction.id': tx.id}, {'$unset': {'transaction': True}})
        d6_cursor.execute('update krisitine.split set tx_id = NULL where tx_id = %s and tx_id is not null;',
                          (tx.id, ))

    d5_session.close()
    d6_cursor.close()


def remove_split(split):
    if isinstance(split, str):
        split = Dict({'id': split})
    if 'id' not in split or split.id is None: return
    coll_split.remove({'id': split.id})
    d5_session = d8757_5.session()
    d5_session.run('match (n{id:{id}}) detach delete n;', {'id': split.id})
    from katherine import d6_config
    d6 = pymysql.connect(**d6_config)
    d6_cursor = d6.cursor()
    d6_cursor.execute('delete from kristine.split where id = %s;', (split.id, ))
    tx = coll_transaction.find_one({'splits.id': split.id})
    if tx is not None:
        for _split in [split for split in tx.splits if 'id' in split]:
            if _split.id == split.id:
                tx.splits.remove(_split)
        coll_transaction.replace_one({'id': tx.id}, tx)
    d5_session.close()
    d6_cursor.close()
    d6.close()


def handle_action_kristine_create_transaction(msg):
    tx = msg.transaction
    dictutils.dec_to_float(tx)
    splits = tx.splits
    if 'type' not in tx:
        tx.type = 'kristine/transaction'
    if 'id' not in tx:
        tx.id = get_id_with_name(tx.type)

    if 'datetime' not in tx:
        tx.datetime = datetime_isoformat(datetime.now())
    if 'date' not in tx:
        tx.date = date_isoformat(parse_datetime(tx.datetime).date())

    if 'num' not in tx:
        tx.num = get_tx_next_num()

    d5_session = d5.session()
    d6.ping(True)
    d6_cursor = d6.cursor()
    from copy import deepcopy
    for split in splits[:]:
        if 'account' not in split or 'id' not in split.account:
            splits.remove(split)
        else:
            if 'type' not in split:
                split.type = 'kristine/split'
            if 'id' not in split:
                split.id = get_id_with_name(split.type)
            for k in list(split.account.keys()):
                if k not in ['type', 'id']:
                    del split.account[k]
            split = deepcopy(split)
            split.transaction = {'id': tx.id, 'type': tx.type}
            if 'description' not in split and 'description' in tx:
                split.description = tx.description
            if 'num' not in split:
                num = get_split_next_num(split.account)
                if num is not None:
                    split.num = num
                elif 'num' in tx:
                    split.num = tx.num

            if 'datetime' not in split and 'datetime' in tx:
                split.datetime = tx.datetime

            split.date = date_isoformat(parse_datetime(split.datetime))

            coll_split.replace_one({'id': split.id}, split, upsert=True)
            split_node = dict({'id': split.id,
                               'datetime': split.datetime,
                               'date': split.date,
                               'num': split.num if 'num' in split else None,
                               'description': split.description if 'description' in split else None,
                               'value': split.value if 'value' in split else None})

            from utils import remove_values_none as remove_nones
            remove_nones(split_node)

            rr = d5_session.run('merge (n{id:{id}}) set n:kristine_split, n = {split};',
                                {'split': split_node, 'id': split.id})
            rr.single()
            rr = d5_session.run('match (split{id:{split_id}}) with split merge (account{id: {account_id}}) '
                                'create unique (split)-[:account]->(account);',
                                {'split_id': split.id, 'account_id': split.account.id})
            rr.single()
            rr = d5_session.run('match (split{id: {id}})-[rel:account]->(account:kristine_account) '
                                'where account.id <> {account_id} delete rel;',
                                {'id': split.id, 'account_id': split.account.id})
            rr.single()

            d6_cursor.execute('insert kristine.split (tx_id, id, datetime, date, num, description, account_id, value) '
                              'values (%(tx_id)s, %(id)s, %(datetime)s, %(date)s, %(num)s, %(description)s, '
                              '%(account_id)s, %(value)s) ON DUPLICATE KEY UPDATE '
                              'tx_id = values(tx_id), datetime = values(datetime), date = values(date), '
                              'num = values(num), account_id = values(account_id), value = values(value);',
                              split_dict_to_columns(split, tx))

    coll_transaction.replace_one({'id': tx.id}, tx, upsert=True)

    tx_node = {'id': tx.id, 'datetime': tx.datetime, 'date': tx.date,
               'num': tx.num if 'num' in tx else None,
               'description': tx.description if 'description' in tx else None}
    rr = d5_session.run('merge (tx{id:{id}}) set tx:kristine_transaction, tx = {tx};', {'id': tx.id, 'tx': tx_node})
    rr.single()

    d6_cursor.execute('insert kristine.transaction (id, datetime, date, num, description) values '
                      '(%(id)s, %(datetime)s, %(date)s, %(num)s, %(description)s) on duplicate key update '
                      'datetime = values(datetime), date=values(date), num=values(num), '
                      'description=values(description);', tx_dict_to_columns(tx))

    splits_id = [split.id for split in splits if 'id' in split]

    coll_split.update_many({'id': {'$nin': splits_id}, 'transaction.id': tx.id}, {'$unset': {'transaction': True}})
    rr = d5_session.run('match (split:kristine_split)-[rel:transaction]->({id:{tx_id}}) '
                        'where not split.id in {splits_id} delete rel;',
                        {'tx_id': tx.id, 'splits_id': splits_id})
    rr.single()
    rr = d5_session.run('match (split:kristine_split)<-[rel:split]-({id:{tx_id}}) '
                        'where not split.id in {splits_id} delete rel;',
                        {'tx_id': tx.id, 'splits_id': splits_id})
    rr.single()
    rr = d5_session.run('match (split)-[rel:transaction]->(tx:kristine_transaction) '
                        'where split.id in {splits_id} and tx.id <> {tx_id} delete rel;',
                        {'splits_id': splits_id, 'tx_id': tx.id})
    rr.single()
    rr = d5_session.run('match (split)<-[rel:split]-(tx:kristine_transaction) '
                        'where split.id in {splits_id} and tx.id <> {tx_id} delete rel;',
                        {'splits_id': splits_id, 'tx_id': tx.id})
    rr.single()
    rr = d5_session.run('match (split) where split.id in {splits_id} '
                        'match (tx{id:{tx_id}}) '
                        'create unique (split)-[:transaction]->(tx) '
                        'create unique (tx)-[:split]->(split);', {'splits_id': splits_id, 'tx_id': tx.id})
    rr.single()

    d6_cursor.execute('update kristine.split set tx_id = NULL where id not in %(splits_id)s and tx_id = %(tx_id)s;',
                      {'splits_id': splits_id, 'tx_id': tx.id})
    d5_session.close()
    d6_cursor.close()
    d6.close()
    return {'transaction': tx}


def handle_action_kristine_register_check_policy(msg):
    check_policy = msg['check_policy']
    if 'document' in check_policy:
        doc = check_policy['document']
        if 'amount' in doc and 'value' not in doc:
            doc['value'] = doc['amount']
            del doc['amount']
    elif 'documents' in check_policy:
        for doc in check_policy['documents']:
            if 'amount' in doc and 'value' not in doc:
                doc['value'] = doc['amount']
                del doc['amount']
    if 'type' not in check_policy:
        check_policy['type'] = 'kristine/check_policy'
    if 'check' in check_policy:
        check = check_policy['check']
        for k in list(check.keys()):
            if k not in ['id', 'type', 'beneficiary', 'account', 'number', 'num', 'date', 'datetime', 'total', 'bank', 'amount']:
                del check[k]
    dictutils.dec_to_float(check_policy)
    coll_check_policy.insert(check_policy)
    del check_policy['_id']
    return {'check_policy': check_policy}


def handle_action_kristine_remove_split(msg):
    if 'split' in msg:
        remove_split(msg.split)
    elif 'splits' in msg:
        for split in msg.splits:
            remove_split(split)


def handle_action_kristine_remove_transaction(msg):
    if 'transaction' in msg:
        remove_transaction(msg.transaction, msg.with_split if 'with_split' in msg else False)
    elif 'transactions' in msg:
        for tx in msg.transactions:
            remove_transaction(tx, msg.with_split if 'with_split' in msg else False)


def handle_find_kristine_check_policy(msg):
    filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'account':
                if isinstance(k1, dict):
                    for k2, v2 in k1.items():
                        if k2 == 'id':
                            if '$or' not in filter:
                                filter['$or'] = list()
                            filter['$or'].append({'account.id': v2})
                            filter['$or'].append({'check.account.id': v2})
    result = list(coll_check_policy.find({}, {'_id': False}))

    return {'result': result}


rr = Pool_Handler()
rr['type_message=action.action=kristine/create_transaction'] = handle_action_kristine_create_transaction
rr['type_message=action.action=kristine/register_check_policy'] =  handle_action_kristine_register_check_policy
rr['type_message=action.action=kristine/remove_split'] = handle_action_kristine_remove_split
rr['type_message=action.action=kristine/remove_splits'] = handle_action_kristine_remove_split
rr['type_message=action.action=kristine/remove_transaction'] = handle_action_kristine_remove_transaction
rr['type_message=action.action=kristine/remove_transactions'] = handle_action_kristine_remove_transaction
rr['type_message=find.type=kristine/check_policy'] = handle_find_kristine_check_policy


if __name__ == '__main__':
    print("I'm kristine.")
    recipient = Recipient()
    recipient.prepare('/kristine', rr)
    recipient.begin_receive_forever()
