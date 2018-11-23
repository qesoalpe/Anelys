from neo4j.v1 import GraphDatabase, basic_auth
from dict import Dict, Dict as dict, List as list
from utils import find_one
import dictutils
from decimal import Decimal
from copy import deepcopy
from katherine import d1
D = Decimal


txs = list()
checks = list()
cfdis = list()
cps = list()


def populate_with_month(month):
    d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

    d5_session = d5.session()
    from datetime import date as date_cls
    if isinstance(month, date_cls):
        month = month.strftime('%Y-%m')
    elif not isinstance(month, str):
        raise Exception('month should be a date_cls or str isodate month YYYY-MM')
    txs.clear()
    cfdis.clear()

    rr = d5_session.run('match (tx:bailey_transaction)-[:check]->(check) '
                        'where tx.date starts with {month} '
                        'return tx.id as id, tx.value as value, tx.description as description, tx.mov_num as mov_num, '
                        'tx.difference as difference, tx.date as date, check.number, check.id;',
                        {'month': month})
    for rc in rr:
        tx = Dict({'id': rc['id'], 'value': -rc['value'], 'description': rc['description'], 'mov_num': rc['mov_num'],
                   'difference': rc['difference'], 'date': rc['date'], 'cfdis': []})
        check = dict({'number': rc['check.number']})
        if rc['check.id']:
            check.id = rc['check.id']

        tx.check = check
        check.tx = tx
        txs.append(tx)

    rr = d5_session.run('match (tx:bailey_transaction)-[:transfer]->() '
                        'where tx.date starts with {month} '
                        'return tx.id as id, tx.value as value, tx.description as description, tx.mov_num as mov_num, tx.difference as difference, tx.date as date;',
                        {'month': month})
    txs.extend([Dict({'id': rc['id'], 'value': -rc['value'], 'description': rc['description'], 'mov_num': rc['mov_num'], 'difference': rc['difference'],
                      'date': rc['date'], 'cfdis': []}) for rc in rr])

    rr = d5_session.run('match ()<-[:check]-(tx:bailey_transaction)-[:cfdi]->(c:haley_cfdi) '
                        'where tx.date starts with {month} with distinct c, tx '
                        'return tx.id as tx_id, c.uuid as uuid, c.folio as folio, c.total as total, '
                        'c.effect as effect, c.datetime as datetime;',
                        {'month': month})
    from utils import remove_values_none

    for tx in txs:
        remove_values_none(tx)

    for rc in rr:
        tx = find_one(lambda x: x.id == rc['tx_id'], txs)
        if tx is None:
            raise Exception('invalid txs')
        cfdi = Dict({'uuid': rc['uuid'], 'total': rc['total'], 'effect': rc['effect'], 'datetime': rc['datetime']})
        if rc['folio'] is not None:
            cfdi.folio = rc['folio']
        tx.cfdis.append(cfdi)
        cfdi.tx = tx
        cfdis.append(cfdi)

    rr = d5_session.run('match ()<-[:transfer]-(tx:bailey_transaction)-[:cfdi]->(c:haley_cfdi) '
                        'where tx.date starts with {month} with distinct c, tx '
                        'return tx.id as tx_id, c.uuid as uuid, c.folio as folio, c.total as total, '
                        'c.effect as effect, c.datetime as datetime;',
                        {'month': month})
    for rc in rr:
        tx = find_one(lambda x: x.id == rc['tx_id'], txs)
        if tx is None:
            raise Exception('invalid txs')
        cfdi = Dict({'uuid': rc['uuid'], 'total': rc['total'], 'effect': rc['effect'], 'datetime': rc['datetime']})
        if rc['folio'] is not None:
            cfdi.folio = rc['folio']
        tx.cfdis.append(cfdi)
        cfdi.tx = tx
        cfdis.append(cfdi)

    dictutils.list_float_to_dec(txs)
    dictutils.list_float_to_dec(cfdis)
    d5_session.close()
    d5.close()


def validate():
    invalids = list()
    for tx in txs:
        cfdis_total = D()
        for cfdi in tx.cfdis:
            if cfdi.effect == 'ingress':
                cfdis_total += cfdi.total
            elif cfdi.effect == 'egress':
                cfdis_total -= cfdi.total
        if 'difference' in tx:
            cfdis_total -= tx.difference
        if tx.value != cfdis_total:
            invalid = Dict({'tx': tx, 'cfdis': tx.cfdis, 'difference': tx.value - cfdis_total})
            invalid.tx = deepcopy(invalid.tx)
            for k in list(invalid.tx.keys()):
                if k not in ['id', 'value', 'description', 'mov_num', 'date']:
                    del invalid.tx[k]
            invalid.cfdis = deepcopy(invalid.cfdis)
            for cfdi in invalid.cfdis:
                for k in list(cfdi.keys()):
                    if k not in ['uuid', 'folio', 'datetime', 'total', 'effect']:
                        del cfdi[k]
            invalids.append(invalid)
    invalids.sort(key=lambda x: x.tx.mov_num)
    return invalids


def populte_cps_with_checks_pending():
    checks_txs = filter(lambda x: 'check' in x, txs)
    for cp in cps:
        if 'check' in cp:
            del cp.check
    cps.clear()
    for tx in checks_txs:
        cfdis_total = D()
        for cfdi in tx.cfdis:
            if cfdi.effect == 'ingress':
                cfdis_total += cfdi.total
            elif cfdi.effect == 'egress':
                cfdis_total -= cfdi.total
        if 'difference' in tx:
            cfdis_total -= tx.difference
        if tx.value != cfdis_total:
            cp = d1.kristine.check_policy.find_one({'check.number': tx.check.number})
            if cp is not None:
                cp.check = tx.check
                tx.check.check_policy = cp
                cps.append(cp)
            else:
                print(tx.check)
                raise Exception('no se encontro la check_policy del check de la transaction')


def auto_relate_checks_with_cfdis():
    d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

    d5_session = d5.session()

    def relate_cfdi_to_check_tx(cfdi):
        if not('type' not in cfdi and 'folio' in cfdi): return
        rr = d5_session.run('match (cfdi:haley_cfdi{folio: {folio}}) '
                            'match (tx{id: {tx_id}})-[:check]->(check) '
                            'merge (tx)-[:cfdi]->(cfdi) '
                            'merge (t)-[:cfdi]->(cfdi);', {'folio': cfdi.folio, 'tx_id': cp.check.tx.id})
        rr.single()

    for cp in cps:
        if 'document' in cp:
            relate_cfdi_to_check_tx(cp.document)
        elif 'documents' in cp:
            for doc in cp.documents:
                relate_cfdi_to_check_tx(doc)
    d5_session.close()
    d5.close()
