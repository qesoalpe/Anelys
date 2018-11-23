from pprint import pprint
from dict import Dict
import pymysql
from neo4j.v1 import GraphDatabase, basic_auth
from utils import find_one

d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))
d5_session = d5.session()

d6 = pymysql.connect(host='comercialpicazo.com', port=3305, user='alejandro', password='5175202', autocommit=True)
d6_cursor = d6.cursor()

account_providers = Dict({'guid': '1927645d6ebfb199c1004863e794d6b7'})
account_storages = Dict({'guid': 'f45d030ab62a53c62b1b563b90519b67'})

accounts_providers = [account_providers]

rr = d5_session.run('match ({guid:{guid}})<-[:parent*]-(account) return account.guid as guid',
                    {'guid': account_providers.guid})
accounts_providers.extend([Dict({'guid': rc['guid']}) for rc in rr])


accounts_storages = [account_storages]

rr = d5_session.run('match ({guid:{guid}})<-[:parent*]-(account) return account.guid as guid',
                    {'guid': account_storages.guid})
accounts_storages.extend([Dict({'guid': rc['guid']}) for rc in rr])

rr = d5_session.run('match (tx:gnucash_transaction)-[:split]->()-[:account]->(account) '
                    'where account.guid in {accounts_guid} and tx.date >= \'2017-01\' '
                    'optional match (doc)<-[:document]-(tx)'
                    'return tx.guid as guid, tx.description as description, doc.id as doc_id, doc.folio as doc_folio, '
                    'doc.datetime as doc_datetime;',
                    {'accounts_guid': [account.guid for account in accounts_storages]})


txs = list()
documents = list()

for rc in rr:
    tx = find_one(lambda x: x.guid == rc['guid'], txs)
    if tx is None:
        tx = Dict({'guid': rc['guid'], 'documents': [], 'description': rc['description']})
        txs.append(tx)
    if rc['doc_id'] is not None:
        doc = find_one(lambda x: x.id == rc['doc_id'], documents)
        if doc is None:
            doc = Dict({'id': rc['doc_id'], 'datetime': rc['doc_datetime']})
            if rc['doc_folio'] is not None:
                doc.folio = rc['doc_folio']
            documents.append(doc)
        tx.documents.append(doc)

rr = d5_session.run('match (doc:bethesda_document_purchase) '
                    'where doc.datetime >= "2017-06" return doc.id as id, doc.folio as folio, doc.datetime as datetime;')

for rc in rr:
    doc = find_one(lambda x: x.id == rc['id'], documents)
    if doc is None:
        doc = Dict({'id': rc['id'], 'datetime': rc['datetime']})
        if rc['folio'] is not None:
            doc.folio = rc['folio']
        documents.append(doc)


if True:
    def ff(document):
        import re
        r = re.compile('\\b' + document.folio + '\\b')
        for tx in txs:
            rr = r.findall(tx.description)
            if len(rr):
                return False
        else:
            return True

    no_pass = list(filter(ff, [document for document in documents if 'folio' in document]))

    pprint(no_pass, width=150)
    pprint(len(no_pass))

if False:
    def ff(document):
        import re
        r = re.compile('\\b' + document.folio + '\\b')
        for tx in txs:
            rr = r.findall(tx.description)
            if len(rr):
                return tx

    for document in [document for document in documents if 'folio' in document]:
        tx = ff(document)
        if tx is not None:
            rr = d5_session.run('match (tx{guid:{tx_guid}})-[:split]->(split) '
                                'match (doc{id:{doc_id}}) '
                                'create unique (tx)-[:document]->(doc) '
                                'create unique (split)-[:document]->(doc);',
                                {'tx_guid': tx.guid, 'doc_id': document.id})
            rr.single()


if False:
    rr = d5_session.run('match (account) where account.guid in {accounts_guid} '
                        'match (doc:bethesda_document_purchase) '
                        'where doc.datetime >= \'2017-06\' and not ((doc)<-[:document]-()-[:split]->()-[:account]->(account)) '
                        'with distinct doc '
                        'return doc.id as id, doc.datetime as datetime, doc.amount as amount, doc.folio as folio;',
                        {'accounts_guid': [account.guid for account in accounts_storages]})

    docs = [Dict({'id': rc['id'], 'datetime': rc['datetime'], 'amount': rc['amount'], 'folio': rc['folio']}) for rc in rr]

    pprint(docs, width=150)
    pprint(len(docs))



# rr = d5_session.run('match (account_provider)<-[:account]-()<-[:split]-(tx:gnucash_transaction)-[:split]->()-[:account]->(account_storage) '
#                     'where tx.date >= "2017-05" and account_provider.guid in {accounts_providers_guid} and account_storage.guid in {accounts_storages_guid} '
#                     'match (doc:bethesda_document_purchase) where doc.datetime >= "2017-05" and tx.description contains doc.folio and '
#                     'not ((doc)<-[:document]-(tx)) '
#                     'with distinct doc return doc.id as id, doc.folio as folio, doc.datetime as datetime;',
#                     {'accounts_providers_guid': [account.guid for account in accounts_providers],
#                      'accounts_storages_guid': [account.guid for account in accounts_storages]})

# rr = d5_session.run('match (tx:gnucash_transaction)-[:split]->()-[:account]->(account_storage) '
#                     'where tx.date >= "2017-05" and account_storage.guid in {accounts_storages_guid} '
#                     'match (doc:bethesda_document_purchase)-[:emitter]->({id:\'61-10\'}) where doc.datetime >= "2017-05" and '
#                     'not tx.description contains doc.folio '
#                     'with distinct doc return doc.id as id, doc.folio as folio, doc.datetime as datetime;',
#                     {'accounts_providers_guid': [account.guid for account in accounts_providers],
#                      'accounts_storages_guid': [account.guid for account in accounts_storages]})