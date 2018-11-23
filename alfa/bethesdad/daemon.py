from sarah.acp_bson import Recipient, Client, Pool_Handler
import anelys
from isodate import datetime_isoformat
from datetime import datetime
import re
import dictutils
from dict import Dict as dict, List as list
from copy import deepcopy
from katherine import d1, d5, d6
from mongoutils import Filter_Mongo


db_bethesda = d1.bethesda

coll_doc_purchase = db_bethesda['document_purchase']
coll_invoice = db_bethesda['invoice']
coll_note_charge = db_bethesda.get_collection('note_charge')
coll_note_credit = db_bethesda['note_credit']
coll_order = db_bethesda['order']
coll_purchase = db_bethesda['purchase']
coll_receipt = db_bethesda['receipt']
coll_remission = db_bethesda['remission']
coll_return_note = db_bethesda['return_note']
coll_sale_note = db_bethesda.get_collection('sale_note')
coll_ticket = db_bethesda['ticket']

colls_document_creditable = [coll_note_credit, coll_return_note, coll_receipt]


agent_perla = Client('/bethesda', '/perla')
agent_valentine = Client('bethesda', 'valentine')


# doc_type_colls = {'bethesda/invoice': coll_}
dict_type_collection = dict()
# dict_type_collection['bethesda/document_purchase'] = coll_doc_purchase
dict_type_collection['bethesda/invoice'] = coll_invoice
dict_type_collection['bethesda/note_charge'] = coll_note_charge
dict_type_collection['bethesda/note_credit'] = coll_note_credit
dict_type_collection['bethesda/order'] = coll_order
dict_type_collection['bethesda/purchase'] = coll_purchase
dict_type_collection['bethesda/receipt'] = coll_receipt
dict_type_collection['bethesda/remission'] = coll_remission
dict_type_collection['bethesda/return_note'] = coll_return_note
dict_type_collection['bethesda/sale_note'] = coll_sale_note
dict_type_collection['bethesda/ticket'] = coll_ticket

list_document_collection_d1 = list(dict_type_collection.values())

me = {'id': '3-1', 'name': 'Alejandro Picazo Loza', 'type': 'reina/person', 'rfc': 'PILA960104HT8'}

# handlers purchase


def set_purchase_in_document_d1(purchase, document):
    if document.type in dict_type_collection:
        dict_type_collection[document.type].update_one(
            {'id': document.id}, {'$set': {'purchase': {'id': purchase.id, 'type': purchase.type}}}
        )


def attach_purchase_and_document_d5(purchase, document):
    d5_session = d5.session()
    rr = d5_session.run('MERGE (purchase{id:{purchase_id}}) MERGE (doc{id:{doc_id}}) '
                        'MERGE (purchase)-[:document]->(doc) MERGE (doc)-[:purchase]->(purchase);',
                        {'purchase_id': purchase.id, 'doc_id': document.id})
    rr.single()
    d5_session.close()


def add_document_to_purchase_d1_isolate(purchase, document):
    doc = dict()
    for k in ['folio', 'id', 'type']:
        if k in document:
            doc[k] = document[k]
    document = doc
    purchase = coll_purchase.find_one({'id': purchase.id}, {'_id': False})

    if 'document' in purchase:
        purchase.documents = [purchase.document, document]
        del purchase.document
    elif 'documents' in purchase:
        purchase.documents.append(document)
    else:
        purchase.document = document

    coll_purchase.replace_one({'id': purchase.id}, purchase)


def handle_action_bethesda_attach_document(msg):
    if 'purchase' in msg and 'document' in msg:
        attach_purchase_and_document_d5(msg.purchase, msg.document)
        set_purchase_in_document_d1(msg.purchase, msg.document)
        add_document_to_purchase_d1_isolate(msg.purchase, msg.document)


def handle_action_bethesda_create_purchase(msg):
    d5_session = d5.session()
    if 'purchase' in msg:
        purchase = msg.purchase

        if 'type' not in purchase:
            purchase.type = 'bethesda/purchase'

        if 'id' not in purchase:
            purchase.id = anelys.get_id_with_name(purchase.type)

        if 'datetime' not in purchase:
            if 'datetime' in msg:
                purchase.datetime = msg.datetime
            else:
                purchase.datetime = datetime_isoformat(datetime.now())

        purchase_node = {'id': purchase['id'], 'datetime': purchase['datetime']}
        if 'amount' in purchase:
            purchase_node['amount'] = purchase['amount']
        elif 'total' in purchase:
            purchase_node['amount'] = purchase['total']
        dictutils.dec_to_float(purchase_node)
        rr = d5_session.run('MERGE (purchase{id: {purchase_id}}) '
                            'MERGE (provider{id:{provider_id}}) '
                            'SET purchase += {purchase}, purchase :bethesda_purchase '
                            'MERGE (purchase)-[:provider]->(provider);',
                            {'purchase_id': purchase.id, 'purchase': purchase_node,
                             'provider_id': purchase.provider.id})
        rr.single()
        d5_session.close()

        def attach_document(doc):
            for k in list(doc.keys()):
                if k not in ['id', 'type', 'datetime', 'folio', 'document_type', 'value']:
                    del doc[k]
            attach_purchase_and_document_d5(purchase, doc)
            set_purchase_in_document_d1(purchase, doc)

        if 'document_value' in purchase:
            attach_document(purchase['document_value'])
        elif 'documents_value' in purchase:
            for doc_value in purchase['documents_value']:
                attach_document(doc_value)

        if 'document' in purchase:
            attach_document(purchase['document'])
        elif 'documents' in purchase:
            for doc in purchase['documents']:
                attach_document(doc)

        if 'storage' in purchase:
            storage = purchase.storage
            for k in list(storage.keys()):
                if k not in ['id', 'type']:
                    del storage[k]

            msg = {'type_message': 'action', 'action': 'valentine/make_movement', 'storage': storage, 'mov_type': 'in',
                   'mov_datetime': purchase.datetime, 'origen': {'id': purchase.id, 'type': purchase.type},
                   'items': purchase['items']}
            answer = agent_valentine(msg)

        msg = {'type_message': 'action', 'action': 'perla/register_purchase_price', 'datetime': purchase.datetime,
               'purchase': {'id': purchase.id, 'type': purchase.type}}
        if 'provider' in purchase:
            msg.provider = purchase.provider
        msg['my_items'] = purchase['items']
        answer = agent_perla.send_msg(msg)
        purchase['items'] = answer['my_items']

        dictutils.dec_to_float(purchase)
        coll_purchase.insert(purchase)
        del purchase._id
        return purchase
    else:
        Exception('the function should include a purchase')


def handle_action_bethesda_edit_purchase(msg):
    pass


def handle_action_bethesda_make_receipt(msg):
    receipt = msg['receipt']
    receipt['id'] = anelys.get_id_with_name('bethesda/receipt')
    receipt['type'] = 'bethesda/receipt'
    if 'datetime' not in receipt:
        receipt['datetime'] = datetime_isoformat(datetime.now())
    dictutils.dec_to_float(receipt)
    coll_receipt.insert(receipt)


def handle_get_bethesda_receipt_without_purchase(msg):
    filter = {'purchase': {'$exists': False}, '$or': [{'provider.id': {'$exists': False}}]}
    if 'query' in msg and 'provider' in msg['query'] and 'id' in msg['query']['provider']:
        filter['$or'].append({'provider.id': msg['query']['provider']['id']})
    return {'result': list(coll_receipt.find(filter, {'_id': False}))}

# end handlers purchase


def ending_create_document_purchase_sub(doc):
    d5_session = d5.session()
    if doc['type'] == 'bethesda/invoice':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_invoice:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/note_charge':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_note_charge:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/note_credit':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_note_credit:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/remission':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_remission:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/return_note':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_return_note:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/sale_note':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_sale_note:bethesda_document_purchase;'
    elif doc['type'] == 'bethesda/ticket':
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_ticket:bethesda_document_purchase;'
    else:
        stmt = 'MERGE (doc{id:{id}}) SET doc += {doc}, doc :bethesda_document_purchase;'
    doc_node = deepcopy(doc)
    for k in list(doc_node.keys()):
        if k not in ['id', 'amount', 'datetime', 'folio', 'total', 'date']:
            del doc_node[k]
    result = d5_session.run(stmt, {'id': doc_node['id'], 'doc': doc_node})
    result.single()
    rr = d5_session.run('match (doc{id:{doc_id}}) '
                        'MERGE (recipient{id:{recipient_id}}) '
                        'CREATE UNIQUE (recipient)<-[:recipient]-(doc);', {'doc_id': doc['id'],
                                                                           'recipient_id': me['id']})
    rr.single()
    if 'cfdi' in doc:
        result = d5_session.run('MERGE (cfdi{uuid:{cfdi_uuid}}) '
                                'MERGE (doc{id:{doc_id}}) '
                                'MERGE (cfdi)-[:attached]->(doc) '
                                'MERGE (doc)-[:cfdi]->(cfdi);',
                                {'cfdi_uuid': doc['cfdi']['uuid'], 'doc_id': doc['id']})
        result.single()
    if 'provider' in doc:
        result = d5_session.run('MERGE (provider{id:{provider_id}})'
                                'MERGE (doc{id:{doc_id}}) '
                                'MERGE (doc)-[:provider]->(provider) '
                                'MERGE (provider)<-[:emitter]-(doc);',
                                {'provider_id': doc['provider']['id'], 'doc_id': doc['id']})
        result.single()
    d5_session.close()

    if 'provider' in doc and 'id' in doc['provider'] and 'type' in doc and 'items' in doc:
        d6.ping(True)
        d6_cursor = d6.cursor()
        stmt = 'insert piper.item_document (provider_id, document_type, sku, description, price) values ' \
               '(%(provider_id)s, %(document_type)s, %(sku)s, %(description)s, %(price)s) on duplicate key update ' \
               'description = values(description), price=values(price);'
        params = {'document_type': doc['type'], 'provider_id': doc['provider']['id']}
        for item in doc['items']:
            if 'sku' in item and 'description' in item and 'price' in item:
                params['sku'] = item['sku']
                params['description'] = item['description']
                params['price'] = item['price']
                d6_cursor.execute(stmt, params)
        d6_cursor.close()


def handle_action_bethesda_create_order(msg):
    order = msg['order']
    if 'type' not in order:
        order['type'] = 'bethesda/order'
    if 'id' not in order:
        order['id'] = anelys.get_id_with_name(order['type'])
    if 'datetime' not in order:
        order['datetime'] = datetime_isoformat(datetime.now())
    order['status'] = 'to_receive'
    dictutils.dec_to_float(order)
    coll_order.insert(order)
    del order['_id']
    return {'order': order}


def handle_action_bethesda_create_invoice(msg):
    invoice = msg['invoice']
    if 'type' not in invoice:
        invoice['type'] = 'bethesda/invoice'
    if 'id' not in invoice:
        invoice['id'] = anelys.get_id_with_name(invoice['type'])
    dictutils.dec_to_float(invoice)
    coll_invoice.insert(invoice)
    del invoice['_id']
    ending_create_document_purchase_sub(invoice)
    return {'invoice': invoice}


def handle_action_bethesda_create_note_charge(msg):
    notecharge = msg['note_charge']
    if 'type' not in notecharge:
        notecharge['type'] = 'bethesda/note_chrage'
    if 'id' not in notecharge:
        notecharge['id'] = anelys.get_id_with_name(notecharge['type'])
    dictutils.dec_to_float(notecharge)
    coll_note_charge.insert_one(notecharge)
    if '_id' in notecharge:
        del notecharge['_id']
    ending_create_document_purchase_sub(notecharge)
    return {'note_charge': notecharge}


def handle_action_bethesda_create_note_credit(msg):
    note_credit = msg['note_credit']
    if 'type' not in note_credit:
        note_credit['type'] = 'bethesda/note_credit'
    if 'id' not in note_credit:
        note_credit['id'] = anelys.get_id_with_name(note_credit['type'])
    dictutils.dec_to_float(note_credit)
    coll_note_credit.insert(note_credit)
    del note_credit['_id']
    ending_create_document_purchase_sub(note_credit)
    return {'note_credit': note_credit}


def handle_action_bethesda_create_receipt(msg):
    pass


def handle_action_bethesda_create_remission(msg):
    remission = msg['remission']
    if 'type' not in remission:
        remission['type'] = 'bethesda/remission'
    if 'id' not in remission:
        remission['id'] = anelys.get_id_with_name('bethesda/remission')
    dictutils.dec_to_float(remission)
    coll_remission.insert(remission)
    del remission['_id']
    ending_create_document_purchase_sub(remission)
    return {'remission': remission}


def handle_action_bethesda_create_return_note(msg):
    returnnote = msg['return_note']
    if 'type' not in returnnote:
        returnnote['type'] = 'bethesda/return_note'
    if 'id' not in returnnote:
        returnnote['id'] = anelys.get_id_with_name(returnnote['type'])
    dictutils.dec_to_float(returnnote)
    coll_return_note.insert(returnnote)
    if '_id' in returnnote:
        del returnnote['_id']
    ending_create_document_purchase_sub(returnnote)
    return {'return_note': returnnote}


def handle_action_bethesda_create_sale_note(msg):
    salenote = msg['sale_note']
    if 'type' not in salenote:
        salenote['type'] = 'bethesda/sale_note'
    if 'id' not in salenote:
        salenote['id'] = anelys.get_id_with_name(salenote['type'])
    dictutils.dec_to_float(salenote)
    coll_sale_note.insert(salenote)
    if '_id' in salenote:
        del salenote['_id']
    ending_create_document_purchase_sub(salenote)
    return {'sale_note': salenote}


def handle_action_bethesda_create_ticket(msg):
    ticket = msg['ticket']
    if 'type' not in ticket:
        ticket['type'] = 'bethesda/ticket'
    if 'id' not in ticket:
        ticket['id'] = anelys.get_id_with_name(ticket['type'])
    dictutils.dec_to_float(ticket)
    coll_ticket.insert(ticket)
    del ticket['_id']
    ending_create_document_purchase_sub(ticket)
    return {'ticket': ticket}


def handle_find_bethesda_order(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'provider':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == 'id':
                            l_filt['provider.id'] = v2
                        elif k2 == 'name':
                            if isinstance(v2, dict):
                                for k3, v3 in v2.items():
                                    if k3 == '!like':
                                        l_filt['provider.name'] = re.compile('.*' + v3.replace(' ', '.*') + '.*', re.I)
            elif k1 == 'datetime':
                pass
            elif k1 == 'status':
                l_filt.status = v1
    result = list(coll_order.find(l_filt, {'_id': False}))
    if 'sort' in msg:
        sort = msg
        if isinstance(sort, list):
            for s in reversed(sort):
                result.sort(key=s[0], reverse=False if s[1] == 1 else True)
    if 'limit' in msg and len(result) > msg.limit:
        result = result[:msg.limit]
    return {'result': result}


def handle_find_bethesda_purchase(msg):
    l_filt = dict()
    if 'query' in msg:
        pass
    return {'result': list(coll_purchase.find(l_filt, {'_id': False}))}


def handle_find_one_bethesda_invoice(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_invoice.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_note_charge(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_note_charge.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_note_credit(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_note_credit.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_remission(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_remission.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_return_note(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_return_note.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_sale_note(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_sale_note.find_one(l_filter, {'_id': False})}


def handle_find_one_bethesda_ticket(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    return {'result': coll_ticket.find_one(l_filter, {'_id': False})}


def handle_find_bethesda_document_purchase(msg):
    filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'provider':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if v2 == 'id':
                            filter['provider.id'] = v2
            elif k1 == 'datetime':
                if isinstance(v1, str):
                    filter['datetime'] = re.compile(v1 + '.*')
                elif isinstance(v1, dict):
                    filter['datetime'] = dict()
                    if '!gt' in v1:
                        filter['datetime']['$gt'] = v1['!gt']
                    if '!lt' in v1:
                        filter['datetime']['$lt'] = v1['!lt']
                    if len(filter['datetime']) == 0:
                        del filter['datetime']

    result = list(coll_invoice.find(filter, {'_id': False}))
    # getting invoices

    # getting notes credit
    result.extend(coll_note_credit.find(filter, {'_id': False}))
    # getting remissions
    result.extend(coll_remission.find(filter, {'_id': False}))
    # getting tickets
    result.extend(coll_ticket.find(filter, {'_id': False}))
    # I'll sort the docs
    result.sort(key=lambda x: x.datetime if 'datetime' in x else '')
    return {'result': result}

    # d5_session = d8757_5_bolt.session()
    # rr = d5_session.run('match (doc:bethesda_document_purchase) '
    #                     'optional match (doc)-[:provider]->(provider) '
    #                     'return doc.id as id, doc.amount as amount, doc.datetime as datetime, doc.folio as folio, '
    #                     'labels(doc) as labels, provider.id as provider_id, provider.name as provider_name, '
    #                     'provider.business_name as provider_business_name order by datetime; ')
    #
    # result = list()
    # labels_types = {'bethesda_invoice': 'bethesda/invoice', 'bethesda_ticket': 'bethesda/ticket',
    #                 'bethesda_remission': 'bethesda/remission', 'bethesda_sale_note': 'bethesda/sale_note',
    #                 'bethesda_note_credit': 'bethesda/note_credit', 'bethesda_return_note': 'bethesda/return_note',
    #                 'bethesda_charge_note': 'bethesda/charge_note'}
    #
    # for rc in rr:
    #     doc = dict()
    #     if rc['id'] is not None:
    #         doc['id'] = rc['id']
    #
    #     if rc['amount'] is not None:
    #         doc['amount'] = rc['amount']
    #
    #     if rc['datetime'] is not None:
    #         doc['datetime'] = rc['datetime']
    #
    #     if rc['folio'] is not None:
    #         doc['folio'] = rc['folio']
    #
    #     if rc['labels'] is not None:
    #         doc['labels'] = rc['labels']
    #         for label in doc['labels']:
    #             if label in labels_types:
    #                 doc['type'] = labels_types[label]
    #                 break
    #
    #     if rc['provider_name'] is not None or rc['provider_id'] is not None:
    #         provider = dict()
    #
    #         if rc['provider_id'] is not None:
    #             provider['id'] = rc['provider_id']
    #
    #         if rc['provider_name'] is not None:
    #             provider['name'] = rc['provider_name']
    #
    #         if rc['provider_business_name'] is not None:
    #             provider['business_name'] = rc['provider_business_name']
    #
    #         doc['provider'] = provider
    #     result.append(doc)
    # d5_session.close()
    # return {'result': result}


def handle_get_bethesda_documents_purchase_without_purchase(msg):
    filter = dict({'purchase': {'$exists': False}})
    for k1, v1 in msg.query.items():
        if k1 == 'provider':
            if isinstance(v1, dict):
                for k2, v2 in v1.items():
                    if k2 == 'id':
                        filter['provider.id'] = v2
            elif isinstance(v1, str):
                filter['provider.id'] = v1

    result = list()
    for coll in list_document_collection_d1:
        result.extend(coll.find(filter, {'_id': False}))

    result.sort(key=lambda x: x.datetime if 'datetime' in x else '')
    return result


def handle_find_bethesda_document_debitable(msg):
    f = Filter_Mongo()
    f.fields.extend(['payment', 'payments', 'purchase', 'provider.id', 'datetime'])
    f.parse_anelys_query(msg.query)

    result = list()
    for coll in [coll_invoice, coll_remission, coll_sale_note, coll_ticket]:
        result.extend(coll.find(f.dict, {'_id': False}))
    result.sort(key=lambda x: x.datetime if 'datetime' in x else '')
    return {'result': result}


rr = Pool_Handler()
rr['type_message=action.action=bethesda/attach_document'] = handle_action_bethesda_attach_document
rr.reg('type_message=action.action=bethesda/create_invoice', handle_action_bethesda_create_invoice)
rr.reg('type_message=action.action=bethesda/create_order', handle_action_bethesda_create_order)
rr.reg('type_message=action.action=bethesda/create_note_charge', handle_action_bethesda_create_note_charge)
rr.reg('type_message=action.action=bethesda/create_note_credit', handle_action_bethesda_create_note_credit)
rr.reg('type_message=action.action=bethesda/create_purchase', handle_action_bethesda_create_purchase)
rr.reg('type_message=action.action=bethesda/create_receipt', handle_action_bethesda_create_receipt)
rr.reg('type_message=action.action=bethesda/create_remission', handle_action_bethesda_create_remission)
rr.reg('type_message=action.action=bethesda/create_return_note', handle_action_bethesda_create_return_note)
rr.reg('type_message=action.action=bethesda/create_sale_note', handle_action_bethesda_create_sale_note)
rr.reg('type_message=action.action=bethesda/create_ticket', handle_action_bethesda_create_ticket)
rr.reg('type_message=action.action=bethesda/make_order', handle_action_bethesda_create_order)
rr.reg('type_message=action.action=bethesda/save_invoice', handle_action_bethesda_create_invoice)
rr.reg('type_message=action.action=bethesda/save_note_credit', handle_action_bethesda_create_note_credit)
rr.reg('type_message=action.action=bethesda/save_remission', handle_action_bethesda_create_remission)
rr.reg('type_message=action.action=bethesda/save_ticekt', handle_action_bethesda_create_ticket)
rr.reg('type_message=find.type=bethesda/document_purchase', handle_find_bethesda_document_purchase)
rr.reg('type_message=find.type=bethesda/order', handle_find_bethesda_order)
rr.reg('type_message=find.type=bethesda/purchase', handle_find_bethesda_purchase)
rr.reg('type_message=find_one.type=bethesda/invoice', handle_find_one_bethesda_invoice)
rr.reg('type_message=find_one.type=bethesda/note_charge', handle_find_one_bethesda_note_charge)
rr.reg('type_message=find_one.type=bethesda/note_credit', handle_find_one_bethesda_note_credit)
rr.reg('type_message=find_one.type=bethesda/remission', handle_find_one_bethesda_remission)
rr.reg('type_message=find_one.type=bethesda/return_note', handle_find_one_bethesda_return_note)
rr.reg('type_message=find_one.type=bethesda/sale_note', handle_find_one_bethesda_sale_note)
rr.reg('type_message=find_one.type=bethesda/ticket', handle_find_one_bethesda_ticket)
rr['type_message=find.type=bethesda/document_debitable'] = handle_find_bethesda_document_debitable
rr.reg('type_message=request.request_type=get.get=bethesda/documents_purchase_without_purchase',
       handle_get_bethesda_documents_purchase_without_purchase)
rr.reg('type_message=request.request_type=get.get=bethesda/receipt_without_purchase',
       handle_get_bethesda_receipt_without_purchase)


if __name__ == '__main__':
    print("I'm bethesda.")
    recipient = Recipient()
    recipient.prepare('/bethesda', rr)
    recipient.begin_receive_forever()
