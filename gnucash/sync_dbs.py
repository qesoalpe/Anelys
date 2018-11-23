import pymysql
from neo4j.v1 import GraphDatabase, basic_auth
from pymongo import MongoClient
from dict import Dict
from sarah import dictutils
from datetime import datetime
from isodate import date_isoformat, datetime_isoformat
print('starting gnucash.sync_dbs')
print('making connections')
d1 = MongoClient('mongodb://comercialpicazo.com')
d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))
d6 = pymysql.connect(host='comercialpicazo.com', port=3305, user='alejandro', password='5175202', autocommit=True)

d1.admin.authenticate('alejandro', '47exI4')

print('connections made')

d6_cursor_dict = d6.cursor(pymysql.cursors.DictCursor)
d6_cursor = d6.cursor()
d5_session = d5.session()

print('buscando ultimo snapshot')

snapshot = d1.gnucash.snapshot.find_one({}, {'_id': False}, sort=[('datetime', -1)])

if snapshot is not None:
    snapshot = Dict(snapshot)
else:
    snapshot = Dict()

stmt = """insert gnucash.split (guid, description, account_guid, tx_guid, value) (select guid, IF(memo != '', memo, NULL) as description, account_guid, tx_guid, value_num / value_denom as value from gnucash.splits where datetime_created > %(splits_datetime)s and guid not in (select guid from gnucash.split));
update gnucash.split inner join gnucash.splits on split.guid = splits.guid set split.description = IF(splits.memo != '', splits.memo, NULL), split.account_guid = splits.account_guid, split.tx_guid = splits.tx_guid, split.value = splits.value_num / splits.value_denom where splits.datetime_modified > %(splits_datetime)s and not splits.datetime_created > %(splits_datetime)s;
delete from gnucash.split where guid not in (select guid from gnucash.splits);"""

if 'splits' in snapshot and 'datetime' in snapshot.splits:
    d6_cursor_dict.execute('select guid, value_num / value_denom as value, memo as description, account_guid, tx_guid '
                           'from gnucash.splits where datetime_created >= %s or datetime_modified >= %s;',
                           (snapshot.splits.datetime, snapshot.splits.datetime))
    splits = [Dict(split) for split in d6_cursor_dict]
    d6_cursor.execute(stmt, {'splits_datetime': snapshot.splits.datetime})
else:
    d6_cursor_dict.execute('select guid, value_num / value_denom as value, memo as description, account_guid, tx_guid '
                           'from gnucash.splits;')
    splits = [Dict(split) for split in d6_cursor_dict]
print(0)
for split in splits:
    if 'description' in split and not split.description:
        del split.description
    split_node = Dict({'guid': split.guid, 'value': split.value})
    if 'description' in split:
        split_node.description = split.description
    dictutils.dec_to_float(split_node)
    rr = d5_session.run('merge (split{guid:{split_guid}}) set split:gnucash_split, split += {split} '
                        'merge (tx{guid:{tx_guid}}) merge (account{guid:{account_guid}}) '
                        'create unique (split)-[:transaction]->(tx), (tx)-[:split]->(split), '
                        '(split)-[:account]->(account);',
                        {'split_guid': split.guid, 'split': split_node, 'tx_guid': split.tx_guid,
                         'account_guid': split.account_guid})
    rr.single()
print(1)
d6_cursor.execute('select guid from gnucash.splits')
splits_guid = [guid for guid, in d6_cursor]

if 'splits' in snapshot and 'snapshot' in snapshot.splits:
    splits_to_delete = list(filter(lambda x: x not in splits_guid, snapshot.splits.snapshot))
    rr = d5_session.run('match (split) where split.guid in {splits_guid} detach delete split;',
                        {'splits_guid': splits_to_delete})
    rr.single()

if 'splits' not in snapshot:
    snapshot.splits = Dict()
print(2)
snapshot.splits.datetime = datetime_isoformat(datetime.now())
snapshot.splits.snapshot = splits_guid

stmt = """insert into gnucash.`transaction` (guid, description, num, date) (select guid, description, IF(num != '', num, NULL) as num, date(post_date) from gnucash.transactions where datetime_created > %(txs_datetime)s and guid not in (select guid from gnucash.transaction)); 
update gnucash.transaction as tx inner join gnucash.transactions as txs on tx.guid = txs.guid set tx.date = date(txs.post_date), tx.description = txs.description, tx.num = IF(txs.num != '', txs.num, NULL) where txs.datetime_modified > %(txs_datetime)s and not txs.datetime_created > %(txs_datetime)s; 
delete from gnucash.transaction where guid not in (select guid from gnucash.transactions);"""

if 'transactions' in snapshot and 'datetime' in snapshot.transactions:
    d6_cursor_dict.execute('select guid, description, num, date(post_date) as date from gnucash.transactions '
                           'where datetime_created >= %s or datetime_modified >= %s',
                           (snapshot.transactions.datetime, snapshot.transactions.datetime))
    txs = [Dict(tx) for tx in d6_cursor_dict]

    d6_cursor.execute(stmt, {'txs_datetime': snapshot.transactions.datetime})
else:
    d6_cursor_dict.execute('select guid, description, num, date(post_date) as date from gnucash.transactions;')
    txs = [Dict(tx) for tx in d6_cursor_dict]
print(3)

for tx in txs:
    try:
        tx.num = int(tx.num)
    except ValueError:
        del tx.num

    tx.date = date_isoformat(tx.date)
    tx_node = Dict({'guid': tx.guid, 'date': tx.date, 'description': tx.description})
    if 'num' in tx:
        tx_node.num = tx.num

    rr = d5_session.run('merge (tx{guid:{guid}}) set tx:gnucash_transaction, tx += {tx};',
                        {'guid': tx.guid, 'tx': tx_node})
print(4)
d6_cursor.execute('select guid from gnucash.transactions')
txs_guid = [guid for guid, in d6_cursor]

if 'transactions' in snapshot and 'snapshot' in snapshot.transactions:
    txs_guid_to_delete = list(filter(lambda x: x not in txs_guid, snapshot.transactions.snapshot))
    rr = d5_session.run('match (tx) where tx.guid in {txs_guid} detach delete tx;', {'txs_guid': txs_guid_to_delete})
    rr.single()
print(5)
if 'transactions' not in snapshot:
    snapshot.transactions = Dict()

snapshot.transactions.snapshot = txs_guid
snapshot.transactions.datetime = datetime_isoformat(datetime.now())



snapshot.datetime = datetime_isoformat(datetime.now())

d1.gnucash.snapshot.insert(snapshot)
print(6)
