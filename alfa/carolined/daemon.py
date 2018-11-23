from sarah.acp_bson import Recipient, Pool_Handler
from sarah import dictutils
import re
from decimal import Decimal as D
import isodate
import datetime
import anelys
from katherine import d1, d6

db_caroline = d1.caroline

coll_account = db_caroline.get_collection('account')
coll_client = db_caroline.get_collection('client')
coll_debt = db_caroline.get_collection('debt')
coll_receipt = db_caroline.get_collection('receipt')
coll_trans = db_caroline.get_collection('transaction')


agent_credit_default = {'id': '3-1', 'name': 'Alejandro Picazo Loza', 'type': 'reina/person'}


def trans_doc_to_columns(trans_doc):
    columns = {'id': trans_doc['id'], 'type': trans_doc['type'], 'datetime': trans_doc['datetime'],
               'value': trans_doc['value']}
    if 'account' in trans_doc:
        if 'id' in trans_doc['account']:
            columns['account_id'] = trans_doc['account']['id']
        else:
            columns['account_id'] = None
        if 'type' in trans_doc['account']:
            columns['account_type'] = trans_doc['account']['type']
        else:
            columns['account_type'] = None
    else:
        columns['account_id'] = None
        columns['account_type'] = None
    if 'debt' in trans_doc:
        debt = trans_doc['debt']
        if 'id' in debt:
            columns['debt_id'] = debt['id']
        else:
            columns['debt_id'] = None
        if 'type' in debt:
            columns['debt_type'] = debt['type']
        else:
            columns['debt_type'] = None
    else:
        columns['debt_id'] = None
        columns['debt_type'] = None
    return columns


def get_account_balance(account):
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('SELECT CAST(IFNULL(SUM(value), 0) AS DECIMAL(15, 2)) FROM caroline.transaction WHERE '
                      'account_id = %s;', (account['id'],))
    balance, = d6_cursor.fetchone()
    d6_cursor.close()
    return balance


def get_debt_balance(debt):
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('SELECT CAST(IFNULL(SUM(value), 0) AS DECIMAL(15, 2)) FROM caroline.transaction WHERE debt_id = %s;',
                      (debt['id'],))
    bb, = d6_cursor.fetchone()
    return bb


def make_transaction(trans):
    d6.ping(True)
    d6_cursor = d6.cursor()
    if 'type' not in trans:
        trans['type'] = 'caroline/transaction'
    if 'id' not in trans:
        trans['id'] = anelys.get_id_with_name(trans['type'])

    if 'account' in trans:
        account = trans['account']
        for k in list(account.keys()):
            if k not in ['id', 'type']:
                del account[k]

    if 'debt' in trans:
        for k in list(trans['debt'].keys()):
            if k not in ['id', 'type']:
                del trans['debt'][k]

    dictutils.dec_to_float(trans)
    coll_trans.insert(trans)
    del trans['_id']
    dictutils.float_to_dec(trans)
    stmt = 'INSERT INTO caroline.transaction (id, type, value, datetime, debt_id, account_id) VALUES (%(id)s, ' \
           '%(type)s, %(value)s, %(datetime)s, %(debt_id)s, %(account_id)s);'
    d6_cursor.execute(stmt, trans_doc_to_columns(trans))
    value = trans['value']
    account = None
    if 'account' in trans and 'id' in trans['account'] and trans['account']['id'] is not None:
        account = coll_account.find_one({'id': trans['account']['id']}, {'_id': False})
        dictutils.float_to_dec(account)

        if 'balance' in account:
            account['balance'] += value
            account['balance_in_hand'] = account['credit_limit'] - account['balance']
            dictutils.dec_to_float(account)
            coll_account.replace_one({'id': account['id']}, account)
            if '_id' in account:
                del account['_id']
            dictutils.float_to_dec(account)
        elif 'request_balance' in account and account['request_balance']:
            account['balance'] = get_account_balance(account)
            if 'credit_limit' in account:
                account['balance_in_hand'] = account['credit_limit'] - account['balance']
    debt = None
    if 'debt' in trans and 'id' in trans['debt'] and trans['debt']['id'] is not None:
        debt = coll_debt.find_one({'id': trans['debt']['id']}, {'_id': False})
        dictutils.float_to_dec(debt)
        debt['balance'] = get_debt_balance(debt)
        if debt['balance'] <= D() and 'expires' in debt:
            del debt['expires']
        if debt['balance'] == D():
            del debt['balance']
            debt['status'] = 'paid'

        dictutils.dec_to_float(debt)
        coll_debt.replace_one({'id': debt['id']}, debt)
        if '_id' in debt:
            del debt['_id']
        dictutils.float_to_dec(debt)
    d6_cursor.close()
    return account, debt


def handle_action_caroline_create_debt(msg):
    debt = msg['debt']
    if 'type' not in debt:
        debt['type'] = 'caroline/debt'
    if 'type' in debt and 'debt_type' not in debt and debt['type'] != 'caroline/debt':
        debt['debt_type'] = debt['type']
        debt['type'] = 'caroline/debt'
    if 'account' in msg:
        account = msg['account']
        debt['account'] = {'id': account['id'], 'type': account['type']}
    else:
        account = debt['account']
        debt['account'] = {'id': account['id'], 'type': account['type']}
    if 'datetime' not in debt and 'datetime' in msg:
        debt['datetime'] = msg['datetime']
    elif 'datetime' not in debt:
        debt['datetime'] = isodate.datetime_isoformat(datetime.datetime.now())
    if 'id' not in debt:
        debt['id'] = anelys.get_id_with_name(debt['type'])
    debt['status'] = 'valid'
    dictutils.dec_to_float(debt)
    coll_debt.insert(debt)
    del debt['_id']
    dictutils.float_to_dec(debt)
    trans = dict()
    if 'datetime' in msg:
        trans['datetime'] = msg['datetime']
    elif 'datetime' in debt:
        trans['datetime'] = debt['datetime']
    else:
        trans['datetime'] = isodate.datetime_isoformat(datetime.datetime.now())
    trans['account'] = {'id': account['id'], 'type': account['type']}
    trans['debt'] = {'id': debt['id'], 'type': debt['type']}
    if 'amount' in debt:
        trans['value'] = debt['amount']
    elif 'total' in debt:
        trans['value'] = debt['total']
    elif 'value' in debt:
        trans['value'] = debt['value']
    account, debt = make_transaction(trans)
    return {'account': account, 'debt': debt}


def handle_action_caroline_create_client(msg):
    client = msg['client']
    if 'type' not in client:
        client['type'] = 'caroline/client'
    if 'id' not in client and client['type'] == 'caroline/client':
        client['id'] = anelys.get_id_with_name(client['type'])
    elif 'id' not in client:
        raise Exception('if client type is distinct at caroline/client it should has id')
    if 'type' in client and client['type'] != 'caroline/client' and 'client_type' not in client:
        client['client_type'] = client['type']
        client['type'] = 'caroline/client'
    fields_allowed = ['id', 'type', 'client_type', 'name', 'business_name', 'address', 'tel', 'contact', 'rfc',
                      'wholesale']
    for k in list(client.keys()):
        if k not in fields_allowed:
            del client[k]
    dictutils.dec_to_float(client)
    coll_client.insert(client)
    del client['_id']
    return {'client': client}


def handle_action_caroline_create_receipt(msg):
    receipt = msg['receipt']
    if 'type' not in receipt:
        receipt['type'] = 'caroline/receipt'
    if 'id' not in receipt:
        receipt['id'] = anelys.get_id_with_name(receipt['type'])
    debited = receipt['debited']
    d6.ping(True)

    def __help(_debited):
        if _debited['type'] == 'caroline/debt':
            debt = coll_debt.find_one({'id': _debited['id']})
            account = debt['account']
            trans = {'debt': debt, 'account': account, 'value': -_debited['value']}
            payment = {'id': receipt['id'], 'type': receipt['type'], 'value': _debited['value']}
            if 'datetime' in _debited:
                trans['datetime'] = _debited['datetime']
                payment['datetime'] = _debited['datetime']
            elif 'datetime' in receipt:
                trans['datetime'] = receipt['datetime']
                payment['datetime'] = receipt['datetime']
            account, debt = make_transaction(trans)
            if 'payment' in debt:
                    debt['payments'] = [debt['payment'], payment]
                    del debt['payment']
            elif 'payments' in debt:
                debt['payments'].append(payment)
            else:
                debt['payment'] = payment
            dictutils.dec_to_float(debt)
            coll_debt.replace_one({'id': debt['id']}, debt)
    if isinstance(debited, dict):
        __help(debited)
    elif isinstance(debited, list):
        for dd in debited:
            __help(dd)

    dictutils.dec_to_float(receipt)
    coll_receipt.insert(receipt)
    if '_id' in receipt:
        del receipt['_id']
    dictutils.float_to_dec(receipt)
    return {'receipt': receipt}


def handle_action_caroline_grant_credit(msg):
    client = msg['client']
    account = None
    if 'account' not in msg:
        client = coll_client.find_one({'id': client['id']}, {'_id': False})
        account = coll_account.find_one({'id': client['id']})
        if account is None:
            account = {'id': client['id'], 'type': 'caroline/account', 'account_type': client['type']}
            if 'business_name' in client:
                account['name'] = client['business_name']
            elif 'name' in client:
                account['name'] = client['name']

        if 'credit_period' in msg:
            account['credit_period'] = msg['credit_period']
        if 'credit_limit' in msg:
            account['credit_limit'] = msg['credit_limit']
        account['request_balance'] = True
        client['credit'] = True
        client['account'] = {'id': account['id'], 'type': account['type']}
        coll_client.replace_one({'id': client['id']}, client)
        dictutils.dec_to_float(account)
        coll_account.replace_one({'id': account['id']}, account, upsert=True)
        if '_id' in account:
            del account['_id']
        dictutils.float_to_dec(account)
    return {'account': {'id': account['id'], 'type': account['type']}}


def handle_action_caroline_register_payment(msg):
    # debt.register_payment(payment)
    payment = msg['payment']
    if 'datetime' not in payment and 'datetime' in msg:
        payment['datetime'] = msg['datetime']
    elif 'datetime' not in payment and 'datetime' not in msg:
        payment['datetime'] = isodate.datetime_isoformat(datetime.datetime.now())

    debt = coll_debt.find_one({'id': msg['debt']['id']}, {'_id': False})
    if 'payment' in debt:
        payments = [debt['payment'], payment]
        del debt['payment']
        debt['payments'] = payments
    elif 'payments' in debt:
        debt['payments'].append(payment)
    else:
        debt['payment'] = payment
    dictutils.dec_to_float(debt)
    coll_debt.replace_one({'id': debt['id']}, debt)
    if '_id' in debt:
        del debt['_id']
    dictutils.float_to_dec(debt)
    trans = {'datetime': payment['datetime'], 'debt': {'id': debt['id'], 'type': debt['type']},
             'account': {'id': debt['account']['id'], 'type': debt['account']['type']}}
    if 'amount' in payment:
        trans['value'] = -payment['amount']
    elif 'total' in payment:
        trans['value'] = -payment['total']
    elif 'value' in payment:
        trans['value'] = -payment['value']
    account, debt = make_transaction(trans)
    return {'debt': debt, 'account': account}

handle_action_caroline_debt_register_payment = handle_action_caroline_register_payment
handle_action_caroline_register_debt = handle_action_caroline_create_debt


def handle_find_caroline_account(msg):
    filt = dict()
    result = list()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'account_type':
                filt['account_type'] = v1
            elif k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.I)
    for doc in coll_account.find(filt, {'_id': False}):
        result.append(doc)
    return {'result': result}


def handle_find_caroline_client(msg):
    filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.I)
    result = list()
    for doc in coll_client.find(filt, {'_id': False}):
        result.append(doc)
    if 'sort' in msg:
        for sort in msg['sort']:
            if sort['field'] == 'name':
                if isinstance(sort['orientation'], (int, bool)):
                    if sort['orientation']:
                        pass
    return {'result': result}


def handle_find_caroline_debt(msg):
    filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'account':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == 'id':
                            filt['account.id'] = v2
                        elif k2 == 'type':
                            filt['account.type'] = v2
            elif k1 == 'account.id':
                filt['account.id'] = v1
            elif k1 == 'account.type':
                filt['account.type'] = v1
            elif k1 == 'status':
                filt['status'] = v1
    result = list()
    for doc in coll_debt.find(filt, {'_id': False}):
        result.append(doc)
    return {'result': result}


def handle_find_one_caroline_account(msg):
    filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                filt['id'] = v1
    return {'result': coll_account.find_one(filt, {'_id': False})}


def handle_find_one_caroline_client(msg):
    filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                filt['id'] = v1
    return {'result': coll_client.find_one(filt, {'_id': False})}


def handle_find_one_caroline_debt(msg):
    filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                filt['id'] = v1
    return {'result': coll_debt.find_one(filt, {'_id': False})}


def handle_get_caroline_account_balance(msg):
    account = msg['account']
    balance = get_account_balance(account)
    reply = {'balance': balance}
    if 'credit_limit' in account:
        reply['balance_in_hand'] = account['credit_limit'] - balance
    return reply


rr = Pool_Handler()
rr.reg('type_message=action.action=caroline/create_debt', handle_action_caroline_create_debt)
rr.reg('type_message=action.action=caroline/create_client', handle_action_caroline_create_client)
rr.reg('type_message=action.action=caroline/create_receipt', handle_action_caroline_create_receipt)
rr.reg('type_message=action.action=caroline/debt/register_payment', handle_action_caroline_debt_register_payment)
rr.reg('type_message=action.action=caroline/grant_credit', handle_action_caroline_grant_credit)
rr.reg('type_message=action.action=caroline/register_debt', handle_action_caroline_register_debt)
rr.reg('type_message=action.action=caroline/register_payment', handle_action_caroline_register_payment)
rr.reg('type_message=find.type=caroline/account', handle_find_caroline_account)
rr.reg('type_message=find.type=caroline/client', handle_find_caroline_client)
rr.reg('type_message=find.type=caroline/debt', handle_find_caroline_debt)
rr.reg('type_message=find_one.type=caroline/account', handle_find_one_caroline_account)
rr.reg('type_message=find_one.type=caroline/client', handle_find_one_caroline_client)
rr.reg('type_message=find_one.type=caroline/debt', handle_find_one_caroline_debt)
rr.reg('type_message=request.request_type=get.get=caroline/account_balance', handle_get_caroline_account_balance)


if __name__ == '__main__':
    print("I'm caroline")
    recipient = Recipient()
    recipient.prepare('/caroline', rr)

    recipient.begin_receive_forever()
