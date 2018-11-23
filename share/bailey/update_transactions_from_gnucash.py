from katherine import d1, d5, d6, pymysql
from dict import Dict as dict, List as list
from copy import deepcopy
from anelys.remote import get_id_with_name
from isodate import date_isoformat
import dictutils
from datetime import date as date_cls


d6.ping(True)
d6_cursor = d6.cursor()
d6_cursor.execute('update bailey.transaction set account_id = "35-3" where account_id is NULL;')
d6_cursor.close()
d6.close()


def update_txs_from_gnucash(date):

    d5_session = d5.session()
    d6.ping(True)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)

    d6_cursor.execute("select * from (select @date:= date(tx.post_date) as date, "
                      "@mov_num := cast(tx.num as int) as mov_num, tx.description, "
                      "round(splits.value_num / splits.value_denom, 2) as value "
                      "from gnucash.splits inner join gnucash.transactions as tx "
                      "on tx.guid = splits.tx_guid "
                      "where account_guid = '139cbb04b26976b10f6d9383aeffd0cd' and tx.num) as t "
                      "where t.date >= %s order by t.mov_num", (date, ))

    gnucash_txs = dict()
    gnucash_txs.list = list([tx for tx in d6_cursor])

    d6_cursor.execute('select * from bailey.transaction where date >= %s order by mov_num', (date, ))

    bailey_txs = dict()
    bailey_txs.list = list([tx for tx in d6_cursor])
    bailey_txs.mov_num = list([tx.mov_num for tx in bailey_txs.list])
    bailey_txs.doc_tx = list()
    bailey_txs.txs_pending = list(deepcopy([tx for tx in gnucash_txs.list if tx.mov_num not in bailey_txs.mov_num]))
    for tx in bailey_txs.txs_pending:
        tx.type = 'bailey/transaction'
        tx.id = get_id_with_name(tx.type)
        if '//' in tx.description:
            p = tx.description.find('//')
            tx.description = tx.description[:p].strip()
        tx.account_num = '0418574306'
        tx.account_id = '35-3'
        tx.bank_id = 'MEX-072'
        d6_cursor.execute('insert ignore bailey.transaction (id, type, date, mov_num, account_id, account_num, '
                          'bank_id, value, description) values '
                          '(%s, %s, %s, %s, %s, %s, %s, %s, %s);',
                          (tx.id, tx.type, tx.date, tx.mov_num, tx.account_id, tx.account_num, tx.bank_id,
                           tx.value, tx.description))

        doc_tx = deepcopy(tx)
        doc_tx.account = {'id': tx.account_id, 'num': tx.account_num, 'bank': {'id': tx.bank_id}}
        del doc_tx.account_id
        del doc_tx.account_num
        del doc_tx.bank_id
        if isinstance(doc_tx.date, date_cls):
            doc_tx.date = date_isoformat(doc_tx.date)
        dictutils.dec_to_float(doc_tx)
        d1.bailey.transaction.insert_one(doc_tx)
        tx_node = dict({'id': doc_tx.id, 'value': doc_tx.value, 'description': doc_tx.description, 'date': doc_tx.date,
                        'mov_num': doc_tx.mov_num})
        rr = d5_session.run('MERGE (tx{id:{tx}.id}) set tx: bailey_transaction, tx += {tx} '
                            'MERGE (account{id: {account_id}}) MERGE (tx)-[:account]->(account);',
                            {'tx': tx_node, 'account_id': doc_tx.account.id})
        rr.single()

    d5_session.close()
    d6_cursor.close()


def create_transfers_from_txs_mov_num(txs_mov_num):
    for mov_num in txs_mov_num[:]:
        if isinstance(mov_num, str):
            txs_mov_num[txs_mov_num.index(mov_num)] = int(mov_num)

    bailey_txs = [tx for tx in d1.bailey.transaction.find({'mov_num': {'$in': txs_mov_num},
                                                           'transfer': {'$exists': False}}, {'_id': False})]
    transfers = list()
    d5_session = d5.session()

    for tx in bailey_txs:
        transfer = dict({'id': get_id_with_name('bailey/transfer'), 'type': 'bailey/transfer',
                         'datetime': tx.date + 'T12:00:00', 'amount': abs(tx.value), 'origen': deepcopy(tx.account),
                         'transaction': {'id': tx.id, 'type': tx.type}})
        for k in list(transfer.origen.keys()):
            if k not in ['id', 'type']:
                del transfer.origen[k]
        tx.transfer = {'id': transfer.id, 'type': transfer.type}
        d1.bailey.transaction.replace_one({'id': tx.id}, tx)
        d1.bailey.transfer.insert_one(transfer)
        transfers.append(transfer)

        transfer_node = dict({'id': transfer.id, 'datetime': transfer.datetime, 'amount': transfer.amount})

        rr = d5_session.run('merge (t{id: {t}.id}) set t :bailey_transfer, t += {t} merge (tx{id: {tx_id}}) '
                            'merge (origen{id: {origen_id}}) '
                            'merge (t)-[:transaction]->(tx) '
                            'merge (tx)-[:transfer]->(t) '
                            'merge (t)-[:origen]->(origen);',
                            {'t': transfer_node, 'tx_id': tx.id, 'origen_id': transfer.origen.id})

        rr.single()

    d5_session.close()


if __name__ == '__main__':
    # update_txs_from_gnucash('2018-01-01')
    # txs_mov_num = [1206, 1196, 1195, 1194, 1193]
    # create_transfers_from_txs_mov_num(txs_mov_num)
    pass