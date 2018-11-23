from neo4j.v1 import GraphDatabase, basic_auth
import pymysql
import anelys
from dict import Dict as dict
from katherine import d1 as d8757_1, d6_config, d1

d8757_5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

d8757_6 = pymysql.connect(**d6_config)

d5_session = d8757_5.session()

d6_cursor = d8757_6.cursor()


def persist_policy(policy):
    import dictutils
    dictutils.dec_to_float(policy)
    if 'type' not in policy:
        policy.type = 'haley/policy'

    if 'id' not in policy:
        policy.id = anelys.get_id_with_name(policy.type)

    coll_policy = d8757_1.haley.policy

    policy_node = dict({'id': policy.id, 'date': policy.date, 'concept': policy.concept, 'num_id': policy.num_id})

    rr = d5_session.run('merge (policy{id:{id}}) set policy: haley_policy, policy += {policy};',
                        {'id': policy.id, 'policy': policy_node})
    rr.single()

    d6_cursor.execute('insert haley.policy (id, type, concept, date) values (%s, %s, %s, %s);',
                      (policy.id, policy.type, policy.concept, policy.date))

    def persist_tx(tx):
        if 'id' not in tx:
            tx.id = anelys.get_id_with_name(tx['type'] if 'type' in tx else 'haley/transaction')
        tx_node = {'debit': tx.debit, 'credit': tx.credit, 'id': tx.id, 'concept': tx.concept}
        rr = d5_session.run('match (policy{id:{policy_id}}) '
                            'merge (account:haley_account{number:{account}.number}) '
                            'merge (tx:haley_transaction{id:{tx}.id}) '
                            'MERGE (policy)-[:transaction]->(tx)-[:account]->(account) '
                            'set tx += {tx};',
                            {'policy_id': policy.id, 'account': tx.account, 'tx': tx_node})
        rr.single()
        d6_cursor.execute('insert haley.transaction (id, policy_id, concept, account_number, debit, credit) values '
                          '(%s, %s, %s, %s, %s, %s);',
                          (tx.id, policy.id, tx.concept, tx.account.number, tx.debit, tx.credit))

        def persist_cfdi(cfdi):
            rr = d5_session.run('merge (tx{id:{tx_id}}) merge (cfdi{uuid:{cfdi_uuid}}) '
                                'merge (tx)-[:cfdi]->(cfdi);',
                                {'tx_id': tx.id, 'cfdi_uuid': cfdi.uuid})
            rr.single()

        if 'voucher' in tx:
            persist_cfdi(tx.voucher)
        elif 'vouchers' in tx:
            for voucher in tx.vouchers:
                persist_cfdi(voucher)
        elif 'cfdi' in tx:
            persist_cfdi(tx.cfdi)
        elif 'cfdis' in tx:
            for cfdi in tx.cfdis:
                persist_cfdi(cfdi)

        def persist_check(check):
            params = dict({'check_number': check.number, 'tx_id': tx.id})

            if 'origen' in check and 'number' in check['origen']:
                params.account_number = check.origen.number
            elif 'account_origen' in check and 'number' in check['account_origen']:
                params.account_number = check.account_origen.number
            elif 'account' in check and 'number' in check['account']:
                params.account_number = check.account.number
            else:
                params.account_number = None

            rr = d5_session.run('merge (account{number:{account_number}}) '
                                'merge (account)<-[:account]-(check:bailey_check{number:{check_number}}) '
                                'with check '
                                'match (tx{id:{tx_id}}) '
                                'MERGE (tx)-[:check]->(check);', params)
            rr.single()
        if 'check' in tx:
            persist_check(tx['check'])
        elif 'check' in tx:
            for check in tx['checks']:
                persist_check(check)

    if 'transactions' in policy:
        for tx in policy.transactions:
            persist_tx(tx)
    elif 'transaction' in policy:
        persist_tx(policy.transaction)

    rr = d5_session.run('match (policy{id:{id}})-[rel:cfdi]->() delete rel;', {'id': policy.id})
    rr.single()

    rr = d5_session.run('match (policy{id:{id}})-[:transaction]->()-[:cfdi]->(cfdi) '
                        'MERGE (policy)-[:cfdi]->(cfdi);', {'id': policy.id})
    rr.single()

    rr = d5_session.run('match (policy{id:{id}})-[rel:check]->() delete rel;', {'id': policy.id})
    rr.single()

    rr = d5_session.run('match (policy{id:{id}})-[:transaction]->()-[:check]->(check) '
                        'MERGE (policy)-[:check]->(check);', {'id': policy.id})
    rr.single()

    coll_policy.replace_one({'id': policy.id}, policy, upsert=True)
    dictutils.float_to_dec(policy)


def persist_policies_dom(policies_dom):
    from xml.dom import minidom
    import os
    if isinstance(policies_dom, minidom.Document):
        policies_dom = policies_dom.documentElement
    elif isinstance(policies_dom, str) and os.path.exists(policies_dom):
        f = open(policies_dom, 'rt', encoding='utf8')
        policies_dom = minidom.parseString(f.read()).documentElement
        f.close()

    month = policies_dom.getAttribute('Anio') + '-' + policies_dom.getAttribute('Mes')

    d6_cursor.execute('delete from haley.transaction '
                      'where policy_id in (select id from haley.policy where date like %s)', (month + '%'))
    d6_cursor.execute('delete from haley.policy where date like %s;', (month + '%'))

    import re
    d1.haley.policy.remove({'date': re.compile(month + '.*')})

    d5_session.run('match (p:haley_policy) WHERE p.date starts with {month} '
                   'OPTIONAL MATCH (p)-[:transaction]->(tx:haley_transaction) '
                   'DETACH DELETE p, tx;', {'month': month})
    from haley import policyutils
    policies_dict = [policyutils.parse_policy_xml(policy_dom)
                     for policy_dom in policies_dom.childNodes if policy_dom.nodeName == 'PLZ:Poliza']
    for policy in policies_dict:
        persist_policy(policy)
