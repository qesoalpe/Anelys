import anelys
from katherine import d1, d6
from datetime import datetime
from isodate import datetime_isoformat
from sarah.acp_bson import Recipient, Pool_Handler
from dict import Dict as dict, List as list
from sarah import dictutils
from decimal import Decimal as D


db_vasya = d1.vasya
coll_account = db_vasya.get_collection('account')
coll_receipt = db_vasya.get_collection('receipt')
coll_transaction = db_vasya.get_collection('transaction')


def get_receipt():
    return {'id': anelys.get_id_with_name('vasya/receipt'), 'type': 'vasya/receipt'}


def to_maria_trans(trans):
    trans_maria = {'id': trans['id'], 'type': trans['type'], 'datetime': trans['datetime']}
    if 'description' in trans:
        trans_maria['description'] = trans['description']
    else:
        trans_maria['description'] = None
    if 'account' in trans:
        trans_maria['account_id'] = trans['account']['id']
        trans_maria['account_type'] = trans['account']['type']
    else:
        trans_maria['account_id'] = None
        trans_maria['account_type'] = None
    if 'value' in trans:
        trans_maria['value'] = trans['value']
    else:
        trans_maria['value'] = None
    if 'token' in trans:
        trans_maria['token'] = trans['token']
    else:
        trans_maria['token'] = None
    return trans_maria


def to_maria_split(split, trans):
    split_maria = {'transaction_id': trans['id'], 'account_id': split['account']['id'],
                   'account_type': split['account']['type'], 'value': split['value']}
    if 'description' in split:
        split_maria['description'] = split['description']
    else:
        split_maria['description'] = None
    return split_maria


def handle_action_vasya_begin_transaction(msg):
    try:
        trans = msg['transaction']
        if 'type' not in trans:
            trans['type'] = 'vasya/transaction'
        if trans['type'] != 'vasya/transaction':
            raise Exception('no se puede iniciar una vasya/transaction con una transaction de otro tipo')
        trans['id'] = anelys.get_id_with_name('vasya/transaction')
        if 'token' not in trans:
            trans['token'] = anelys.get_id_with_name('vasya/token')
        if 'datetime' not in trans and 'datetime' in msg:
            trans['datetime'] = msg['datetime']
        else:
            trans['datetime'] = datetime_isoformat(datetime.now())
    
        d6.ping(True)
        d6_cursor = d6.cursor()
        trans_maria = {'id': trans['id'], 'type': trans['type'], 'datetime': trans['datetime'], 'token': trans['token']}
        if 'description' in trans:
            trans_maria['description'] = trans['description']
        else:
            trans_maria['description'] = None
        if 'account' in trans:
            trans_maria['account_id'] = trans['account']['id']
            trans_maria['account_type'] = trans['account']['type']
        else:
            trans_maria['account_id'] = None
            trans_maria['account_type'] = None
        if 'value' in trans:
            trans_maria['value'] = trans['value']
        else:
    
            trans_maria['value'] = None
        trans_maria['token'] = trans['token']
    
        d6_cursor.execute('INSERT vasya.transaction(id, type, datetime, description, account_id, account_type, value, '
                          'token) VALUES (%(id)s, %(type)s, %(datetime)s, %(description)s, %(account_id)s, '
                          '%(account_type)s, %(value)s, %(token)s);', trans_maria)
        dictutils.dec_to_float(trans)
        coll_transaction.insert(trans)
        if '_id' in trans:
            del trans['_id']
        d6_cursor.close()
        return {'transaction': trans}
    except Exception as e:
        print(e)


def handle_action_vasya_commit_transaction(msg):
    try:
        trans = msg['transaction']
        if 'token' in trans:
            del trans['token']
        trans_maria = to_maria_trans(trans)
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('UPDATE vasya.transaction SET value = %(value)s, account_id = %(account_id)s, '
                          'account_type = %(account_type)s, token = %(token)s, description = %(description)s '
                          'WHERE id = %(id)s;', trans_maria)
        dictutils.dec_to_float(trans)
        coll_transaction.replace_one({'id': trans['id']}, trans)
        d6_cursor.close()
        return {'transaction': trans}
    except Exception as e:
        print(e)


def handle_action_vasya_make_transaction(msg):
    trans = msg['transaction']
    if 'datetime' not in trans and 'datetime' in msg:
        trans['datetime'] = msg['datetime']
    elif 'datetime' not in trans:
        trans['datetime'] = datetime_isoformat(datetime.now())
    if 'type' not in trans:
        trans['type'] = 'vasya/transaction'
    if trans['type'] != 'vasya/transaction':
        raise Exception('No es posible manejar transaction distintia a vasya/transaction')
    if 'id' not in trans:
        trans['id'] = anelys.get_id_with_name(trans['type'])
    d6.ping(True)
    d6_cursor = d6.cursor()
    if 'splits' in trans:
        balance = D()
        for split in trans['splits']:
            balance += split['value']
        if balance != D(0):
            raise Exception('no es posible hacer una transaction con splits y que no se cumpla la partida doble')
        for split in trans['splits']:
            d6_cursor.execute('INSERT vasya.split (transaction_id, account_id, account_type, description, value) '
                              'VALUES (%(transaction_id)s, %(account_id)s, %(account_type)s, %(description)s, '
                              '%(value)s);', to_maria_split(split, trans))
    d6_cursor.execute('INSERT vasya.transaction (id, type, datetime, description, account_id, account_type, value, '
                      'token) VALUES (%(id)s, %(type)s, %(datetime)s, %(description)s, %(account_id)s, '
                      '%(account_type)s, %(value)s);', to_maria_trans(trans))
    d6_cursor.close()
    dictutils.dec_to_float(trans)
    coll_transaction.insert(trans)
    del trans['_id']
    dictutils.float_to_dec(trans)
    return {'transaction': trans}


def handle_find_vasya_account(msg):
    l_filt = dict()
    result = list()
    for doc in coll_account.find(l_filt, {'_id': False}):
        result.append(doc)
    if 'projection' in msg:
        projection = msg['projection']
        if 'balance' in projection:
            for account in result:
                if projection['balance']:
                    if 'balance' not in account:
                        account['balance'] = get_vasya_account_balance(account)
                else:
                    if 'balance' in account:
                        del account['balance']
    return {'result': result}


def handle_find_one_vasya_account(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filt['id'] = v1
    return {'result': coll_account.find_one(l_filt, {'_id': False})}


def get_vasya_account_balance(account):
    d6.ping(True)
    d6_cursor = d6.cursr()
    d6_cursor.execute('SELECT CAST(IFNULL(SUM(value), 0) AS DECIMAL(15,2)) FROM vasya.transaction WHERE '
                      'account_id = %s LIMIT 1', (account['id'],))
    balance, = d6_cursor.fetchone()

    d6_cursor.execute('SELECT CAST(IFNULL(sum(value), 0) AS DECIMAL(15, 2)) FROM vasya.split WHERE account_id = %s '
                      'LIMIT 1;', (account['id'],))
    balance += d6_cursor.fetchone()[0]
    d6_cursor.close()
    return balance


def get_account_balance(account):
    return get_vasya_account_balance(account)


def handle_get_vasya_account_balance(msg):
    balance = get_vasya_account_balance(msg['account'])

    return {'balance': balance}


handler = Pool_Handler()
rr = handler
rr['type_message=action.action=vasya/begin_transaction'] = handle_action_vasya_begin_transaction
rr['type_message=action.action=vasya/commit_transaction'] = handle_action_vasya_commit_transaction
rr['type_message=action.action=vasya/make_transaction'] = handle_action_vasya_make_transaction
rr['type_message=find.type=vasya/account'] = handle_find_vasya_account
rr['type_message=find_one.type=vasya/account'] = handle_find_one_vasya_account
rr['type_message=request.request_type=get.get=vasya/account_balance'] = handle_get_vasya_account_balance

if __name__ == '__main__':
    recipient = Recipient()
    recipient.prepare('vasya', handler)
    recipient.begin_receive_forever()
