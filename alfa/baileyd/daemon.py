from sarah.acp_bson import Client, Recipient, Pool_Handler
import dictutils
import anelys
from katherine import d1, d5, d6
from copy import deepcopy

db_bailey = d1.bailey
coll_account = db_bailey.get_collection('account')
coll_check = db_bailey['check']
coll_transaction = db_bailey.get_collection('transaction')
coll_transfer = db_bailey.get_collection('transfer')


agent_kristine = Client('/bailey', '/kristine')

bank_default = {'id': 'MEX-072'}
account_default = {'num': '0418574306', 'id': '35-3'}


def account_columns_to_doc(account):
    doc = dict()
    if account.type is not None:
        doc.type = account.type

    if account.titular_id is not None or account.itular_name is not None:
        titular = dict()
        if account.titular_type is not None:
            titular.type = account.type
        if account.titular_id is not None:
            titular.id = account.titular_id

        if account.titular_name is not None:
            titular.name = account.titular_name

        doc.titular = titular
    if account.number is not None:
        doc.num = account.number
    if account.clabe is not None:
        doc.clabe = account.clabe

    if account.bank_id is not None:
        bank = dict()
        bank.id = account.bank_id
        if 'bank_name' in account and account.bank_name is not None:
            bank.name = account.bank_name

        doc.bank = bank
    return doc


def tx_doc_to_columns(tx):
    columns = dict({'id': tx.id if 'id' in tx else None,
                    'type': tx.type if 'type' in tx else None,
                    'date': tx.date if 'date' in tx else None,
                    'datetime': tx.datetime if 'datetime' in tx else None,
                    'mov_num': tx.mov_num if 'mov_num' in tx else None,
                    'description': tx.description if 'description' in tx else None,
                    'value': tx.value if 'value' in tx else None})
    if 'account' in tx:
        account = tx.account
        columns.account_num = account.number if 'number' in account else account.num if 'num' in account else None
        columns.account_id = account.id if 'id' in account else None
    else:
        columns.account_num = None
        columns.account_id = None

    if 'bank' in tx:
        bank = tx.bank
        columns.bank_id = bank.id if 'id' in bank else None
    elif 'account' in tx and 'bank' in tx.account:
        bank = tx.account.bank
        columns.bank_id = bank.id if 'id' in bank else None
    else:
        columns.bank_id = None

    return columns


trans_doc_to_columns = tx_doc_to_columns
transaction_doc_to_columns = tx_doc_to_columns


def persist_transaction(trans):
    d5_session = d5.session()
    d6.ping(True)
    d6_cursor = d6.cursor()

    if 'type' not in trans:
        trans.type = 'bailey/transaction'
    if 'id' not in trans:
        trans.id = anelys.get_id_with_name(trans.type)

    stmt = 'insert bailey.transaction (id, type, date, mov_num, account_id, account_num, bank_id, value, description) ' \
           'VALUES (%(id)s, %(type)s, %(date)s, %(mov_num)s, %(account_id)s, %(account_num)s, %(bank_id)s, %(value)s, %(description)s) ' \
           'on duplicate key update type=values(type), date=values(date), mov_num=values(mov_num), ' \
           'account_id=values(account_id), account_num=values(account_num), bank_id=values(bank_id), description=values(description);'
    trans_columns = trans_doc_to_columns(trans)
    d6_cursor.execute(stmt, trans_columns)
    dictutils.dec_to_float(trans)
    dictutils.dec_to_float(trans_columns)
    coll_transaction.replace_one({'id': trans.id}, trans, upsert=True)
    if '_id' in trans:
        del trans._id

    trans_node = {'id': trans_columns.id, 'value': trans_columns.value, 'date': trans_columns.date,
                  'description': trans_columns.description, 'mov_num': trans_columns.mov_num}

    d5_session.run('MERGE (bank{id:{bank_id}}) '
                   'MERGE (account{number:{account_number}})-[:bank]->(bank) '
                   'MERGE (trans{id:{trans_id}})-[:account]->(account) '
                   'SET trans :bailey_transaction, trans += {trans};',
                   {'bank_id': trans_columns['bank_id'], 'account_number': trans_columns['account_num'],
                    'trans_id': trans_columns['id'], 'trans': trans_node})
    d6_cursor.close()
    d5_session.close()
    dictutils.float_to_dec(trans)
    return trans


def handle_action_bailey_charge_check(msg):
    trans = msg.transaction

    check = msg.check
    if 'account' in msg:
        account = msg.account
    elif 'account' in check:
        account = check.account
    else:
        raise Exception('action should contains an account')

    trans.account = account
    if 'bank' in msg and 'bank' not in account:
        account.bank = msg.bank
    elif 'bank' not in account and 'bank' in check:
        account.bank = check.bank
    else:
        raise Exception('action should contains a bank')

    if 'value' not in trans and 'amount' in check:
        trans['value'] = - check['amount']
    elif 'value' not in trans:
        raise Exception('action should contains some value or amount')

    trans = persist_transaction(trans)

    d5_session = d5.session()

    rr = d5_session.run('MATCH (trans:bailey_transaction{id:{trans_id}})-[:account]->(account) '
                        'MERGE (check{number:{check_number}})-[:account]->(account) '
                        'MERGE (trans)-[:check]->(check) '
                        'SET check.status = "charged";', {'trans_id': trans['id'], 'check_number': check['number']})
    rr.single()
    d5_session.close()
    check.status = 'charged'
    charge = dict()
    if 'datetime' in trans:
        charge.date = trans.datetime
    elif 'date' in trans:
        charge.date = trans.date
    if 'id' in trans:
        charge.transaction = {'id': trans.id}
    check.charge = charge
    dictutils.dec_to_float(check)
    coll_check.replace_one({'number': check.number, 'account.num': check.account.num, 'bank.id': check.bank.id},
                           check, upsert=True)
    if '_id' in check:
        del check._id
    dictutils.float_to_dec(check)

    return {'check': check, 'transaction': trans}


def handle_action_bailey_check_deliver(msg):
    if 'check_policy' in msg:
        pass
    elif 'check' in msg:
        check = msg.check
        if 'account' not in check:
            check.account = deepcopy(account_default)
        if 'bank' not in check:
            check.bank = bank_default
        if 'status' not in check:
            check.status = 'delivered'
        dictutils.dec_to_float(check)
        coll_check.insert_one(check)
        if '_id' in check:
            del check._id
        d5_session = d5.session()
        check_node = {'number': check.number, 'amount': check.amount, 'date': check.date}

        rr = d5_session.run('MERGE (bank{id:{bank_id}}) '
                            'MERGE (account{number:{account_number}})-[:bank]->(bank) '
                            'MERGE (check{number:{check_number}})-[:account]->(account) '
                            'SET check :bailey_check, check += {check};',
                            {'bank_id': check.bank.id, 'account_number': check.account.num,
                             'check_number': check.number, 'check': check_node})
        rr.single()
        if 'beneficiary' in check and 'id' in check.beneficiary and check.beneficary.id is not None:
            rr = d5_session.run('MATCH (check{number:{check_number}})-[:account]->(account{number:{account_number}})-[:bank]->(bank{id:{bank_id}}) '
                                'MERGE (beneficiary{id:{beneficiary_id}}) '
                                'CREATE UNIQUE (check)-[:beneficiary]->(beneficiary);',
                                {'bank_id': check.bank.id, 'account_number': check.account.num,
                                 'check_number': check.number, 'beneficiary_id': check.beneficiary.id})
            rr.single()
        check_policy = {'check': check}
        def __help(_doc):
            if 'id' in _doc:
                rr = d5_session.run('MATCH (check{number:{check_number}})-[:account]->(account{number:'
                                    '{account_number}})-[:bank]->(bank{id:{bank_id}}) '
                                    'MERGE (check)-[:policy]->(policy:kristine_policy)-[:check]->(check) '
                                    'MERGE (doc{id:{doc_id}}) '
                                    'CREATE UNIQUE (policy)-[:document]->(doc)'
                                    'OPTIONAL MATCH (doc)<-[:attached]-(cfdi:haley_cfdi) '
                                    'CREATE UNIQUE (policy)-[:cfdi]->(doc);',
                                    {'bank_id': check.bank.id, 'account_number': check.account.num,
                                     'check_number': check.number, 'doc_id': _doc.id})
                rr.single()
            elif 'folio' in _doc and _doc.folio != 'descuadre' and 'beneficiary' in check and 'id' in check.beneficiary and check.beneficary is not None:
                rr = d5_session.run('MATCH (check{number:{check_number}})-[:account]->(account{number:'
                                    '{account_number}})-[:bank]->(bank{id:{bank_id}}) '
                                    'MERGE (beneficiary{id:{beneficiary}}) '
                                    'MERGE (check)-[:policy]->(policy:kristine_policy)-[:check]->(check) '
                                    'WITH beneficiary, policy '
                                    'MERGE (doc{folio:{doc_folio}})-[:emitter]->(beneficiary) '
                                    'WITH policyy, doc '
                                    'CREATE UNIQUE (policy)-[:document]->(doc) '
                                    'WITH doc '
                                    'OPTIONAL MATCH (doc)<-[:attached]-(cfdi:haley_cfdi) '
                                    'CREATE UNIQUE (policy)-[:cfdi]->(doc);',
                                    {'bank_id': check.bank.id, 'account_number': check.account.num,
                                     'check_number': check.number, 'doc_folio': _doc.folio})
                rr.single()

        if 'document' in msg:
            check_policy.document = msg.document
        elif 'documents' in msg:
            check_policy.documents = msg.documents
        msg = {'type_message': 'action', 'action': 'kristine/register_check_policy',
               'check_policy': check_policy}
        d5_session.close()
        return agent_kristine.send_msg(msg)


def handle_action_bailey_create_transfer(msg):
    transfer = msg.transfer
    if 'type' not in transfer:
        transfer.type = 'bailey/transfer'

    if 'id' not in transfer:
        transfer.id = anelys.get_id_with_name(transfer.type)
    dictutils.dec_to_float(transfer)
    coll_transfer.insert_one(transfer)
    if '_id' in transfer: del transfer._id

    tx = None


def handle_find_bailey_account(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'titular':
                for k2, v2 in v1.items():
                    if k2 == 'id':
                        l_filter['titular.id'] = v2
    result = [doc for doc in coll_account.find(l_filter, {'_id': False})]
    return {'result': result}


def handle_find_bailey_check(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'status':
                if isinstance(v1, str):
                    l_filt['status'] = v1
                elif isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!nin':
                            if isinstance(v2, list):
                                l_filt['status'] = {'$nin': v2}
    result = [doc for doc in coll_check.find(l_filt, {'_id': False})]
    return {'result': result}


rr = Pool_Handler()
rr.reg('type_message=action.action=bailey/charge_check', handle_action_bailey_charge_check)
rr.reg('type_message=action.action=bailey/check_deliver', handle_action_bailey_check_deliver)
rr.reg('type_message=find.type=bailey/check', handle_find_bailey_check)
read_msg = rr

if __name__ == '__main__':
    print("I'm bailey")
    recipient = Recipient()
    recipient.prepare('/bailey', read_msg)
    recipient.begin_receive_forever()
