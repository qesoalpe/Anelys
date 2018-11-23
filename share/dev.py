from neo4j.v1 import GraphDatabase, basic_auth
from pprint import pprint
from decimal import Decimal


d8757_5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))
d5_session = d8757_5.session()

cfdis = list()
tps = list()
txs = list()


def get_txs(_month):
    rr = d5_session.run('match (tx:bailey_transaction)-[:check]->() where tx.date starts with {month} '
                        'return tx.id as id, tx.date as date, tx.description as description, tx.value as value, '
                        'tx.mov_num as mov_num;',
                        {'month': _month})
    _txs = list()
    for rc in rr:
        _txs.append({'id': rc['id'], 'date': rc['date'], 'description': rc['description'], 'value': rc['value'],
                     'mov_num': rc['mov_num']})
    return _txs


def get_tx(tx):
    for _tx in txs:
        if _tx['id'] == tx['id']:
            return _tx
    else:
        txs.append(tx)
        return tx


def ensure_cfdi(cfdi):
    for _cfdi in cfdis:
        if _cfdi['uuid'] == cfdi['uuid']:
            return _cfdi
    else:
        cfdis.append(cfdi)
        return cfdi


def get_taxpayer(rfc):
    for tp in tps:
        if tp['rfc'] == rfc:
            return tp
    else:
        tp = {'rfc': rfc}
        tps.append(tp)
        return tp


def inflate_cfdis(_txs):
    for _tx in _txs:
        rr = d5_session.run('match ({id:{id}})-[:cfdi]->(cfdi:haley_cfdi)-[:emitter]->(emitter) return cfdi.uuid as uuid, '
                                                'cfdi.total as total, cfdi.datetime as datetime, cfdi.folio as folio, cfdi.voucher_effect as voucher_effect, '
                                                'emitter.rfc as emitter_rfc;',
                                                {'id': _tx['id']})

        cfdis = list()
        for rc in rr:
            cfdi = {'uuid': rc['uuid'], 'datetime': rc['datetime'], 'voucher_effect': rc['voucher_effect'], 'total': rc['total']}
            if rc['folio'] is not None:
                cfdi['folio'] = rc['folio']
            cfdi = ensure_cfdi(cfdi)
            if 'emitter' not in cfdi and rc['emitter_rfc'] is not None:
                cfdi['emitter'] = get_taxpayer(rc['emitter_rfc'])
            cfdis.append(cfdi)

        if len(cfdis) == 1:
            _tx['cfdi'] = cfdis[0]
        elif len(cfdis) > 1:
            _tx['cfdis'] = cfdis


def inflate_txs(cfdi):
    rr = d5_session.run('match (cfdi:haley_cfdi{uuid:{uuid}})<-[:cfdi]-(tx:bailey_transaction) return tx.id as id, tx.value as value, tx.date as date, tx.description as description, tx.mov_num as mov_num;',
                                            {'uuid': cfdi['uuid']})
    txs = list()
    for rc in rr:
        tx = get_tx({'id': rc['id'], 'value': rc['value'], 'description': rc['description'], 'mov_num': rc['mov_num']})

        txs.append(tx)
    if len(txs) == 1:
        cfdi['tx'] = txs[0]
    elif len(txs) > 1:
        cfdi['txs'] = txs


def validation_1():
    # (cfdi)<-[:cfdi]-(tx) count 1
    no_pass = list()
    for cfdi in cfdis:
        if 'txs' in cfdi and len(cfdi['txs']) > 1:
            no_pass.append(cfdi)
    return no_pass


def validation_2():
    # (tx)-[:cfdi]->(cfdi)-[:emitter]->(emitter) emitter unique
    no_pass = list()
    for tx in txs:
        emitter = None
        if 'cfdis' in tx:
            for cfdi in tx['cfdis']:
                if 'emitter' in cfdi:
                    if emitter is not None:
                        if cfdi['emitter']['rfc'] != emitter['rfc']:
                            no_pass.append(tx)
                            break
                    else:
                        emitter = cfdi['emitter']
    return no_pass


def validation_3():
    # tx.value == sum(cfdi.total)
    no_pass = list()
    # {'tx': tx, 'diference': diference}
    from sarah.acp_bson import dictutils
    dictutils.list_float_to_dec(txs)
    for tx in txs:
        total_cfdis = Decimal()
        if 'cfdi' in tx:
            if tx['cfdi']['voucher_effect'] == 'ingress':
                total_cfdis = tx['cfdi']['total']
            elif tx['cfdi']['voucher_effect'] == 'egress':
                total_cfdis = -tx['cfdi']['total']
        elif 'cfdis' in tx:
            for cfdi in tx['cfdis']:
                if cfdi['voucher_effect'] == 'ingress':
                    total_cfdis += cfdi['total']
                elif cfdi['voucher_effect'] == 'egress':
                    total_cfdis -= cfdi['total']
        if total_cfdis != -tx['value']:
            no_pass.append({'tx': tx, 'difference': -tx['value'] - total_cfdis})
    return no_pass


def validation_4():
    # (tx)-[:cfdi]->(cfdi)-[:emitter]->(emitter)<-[:beneficiary]-(check)<-[:check]-(tx)
    no_pass = list()

    return no_pass


def validate():
    validation = dict()
    no_pass = validation_1()
    if len(no_pass) > 0:
        validation['validation_1'] = {'no_pass': no_pass}
    no_pass = validation_2()
    if len(no_pass) > 0:
        validation['validation_2'] = {'no_pass': no_pass}
    no_pass = validation_3()
    if len(no_pass) > 0:
        validation['validation_3'] = {'no_pass': no_pass}
    no_pass = validation_4()
    if len(no_pass) > 0:
        validation['validation_4'] = {'no_pass': no_pass}
    return validation


def populate_from_txs_in_month(month):
    txs.clear()
    tps.clear()
    cfdis.clear()

    txs.extend(get_txs(month))

    inflate_cfdis(txs)

    for cfdi in cfdis:
        inflate_txs(cfdi)

    for tp in tps:
        rr = d5_session.run('match (tp{rfc:{rfc}}) return tp.name as name limit 1;', {'rfc': tp['rfc']})
        rc = rr.single()
        if rc is not None and rc['name'] is not None:
            tp['name'] = rc['name']


if __name__ == '__main__':
    pprint(txs)
    pprint(tps)
    pprint(cfdis)
