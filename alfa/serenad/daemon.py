from sarah.acp_bson import Recipient, Client, Pool_Handler
import anelys
from isodate import datetime_isoformat
from datetime import datetime
from sarah import dictutils
from dict import Dict as dict, List as list
import re
from serenad import events
from serenad import models
from katherine import d1, d5
from mongoutils import Filter_Mongo


db_serena = d1.serena

coll_order = db_serena.get_collection('order')
coll_product = db_serena.get_collection('product')
coll_product_set = db_serena.get_collection('product_set')
coll_remission = db_serena.get_collection('remission')
coll_sale = db_serena.get_collection('sale')
coll_sale_note = db_serena.get_collection('sale_note')
coll_store = db_serena.get_collection('store')
coll_ticket = db_serena.get_collection('ticket')

agent_ella = Client('/serena', '/ella')
agent_itzamara = Client('/serena', '/itzamara')
agent_perla = Client('/serena', '/perla')
agent_valentine = Client('/serena', '/valentine')

map_collection = {'serena/order': coll_order,
                  'serena/product': coll_product,
                  'serena/ticket': coll_ticket,
                  'serena/sale_note': coll_sale_note,
                  'serena/sale': coll_sale,
                  'serena/store': coll_store}


local_store = current_store = coll_store.find_one({'id': '42-3'})


def __handle_action_serena_close_sale_ver_1(msg):
    sale = msg.sale
    doc_items = list()
    for item in sale['items']:
        if 'selected_with' in item:
            del item.selected_with
        doc_item = dict()
        doc_item.sku = item.sku
        doc_item.quanty = item.quanty
        doc_item.description = item.description
        doc_item.price = item.price.value if isinstance(item.price, dict) and 'value' in item.price else item.price
        doc_item.amount = item.quanty * doc_item.price
        doc_items.append(doc_item)
    make_inventory_movement = False
    if 'make_inventory_movement' in msg:
        make_inventory_movement = msg.make_inventory_movement
    if 'id' not in sale:
        sale.id = anelys.get_id_with_name('serena/sale')
    if 'type' not in sale:
        sale.type = 'serena/sale'
    if 'datetime' not in sale:
        sale.datetime = datetime_isoformat(datetime.now())
    required = 'serena/ticket'
    if 'document_sale_required' in msg:
        required = msg.document_sale_required
    if 'order' in sale:
        order = sale.order
        order_projected = {'id': order.id, 'type': order.type}
        msgevent = {'type_message': 'event', 'event': 'serena/order/sold',
                    'order': order_projected, 'sale': {'id': sale.id, 'type': sale.type}}
        agent_ella.send_msg(msgevent)
    elif 'orders' in sale:
        orders_pro = list()
        for order in sale['orders']:
            orders_pro.append({'id': order.id, 'type': order.type})
        msgevent = {'type_message': 'event', 'event': 'serena/order/sold',
                    'orders': orders_pro, 'sale': {'id': sale.id, 'type': sale.type}}
        agent_ella.send_msg(msgevent)

    def _help_make_inventory_mov(docsale):
        msgact = {'type_message': 'action', 'action': 'valentine/make_movement', 'mov_type': 'out', 'storage': None,
                  'items': doc_items, 'origen': {'id': docsale.id, 'type': docsale.type}}
        agent_valentine.send_msg(msgact)

    if required == 'serena/remission':
        remission = models.remission.create()
        remission.datetime = sale.datetime
        remission.client = sale.client
        if 'home_delivery' in sale and 'address' in sale.home_delivery:
            remission.address = sale.home_delivery.address
        remission['items'] = doc_items
        doc_projected = {'id': remission.id, 'type': remission.type,
                         'amount': remission.amount}
        dictutils.dec_to_float(remission)
        coll_remission.replace_one({'id': remission.id}, remission)
        sale.document_sale = doc_projected
        remission.sale = {'id': sale.id, 'type': sale.type}
        dictutils.dec_to_float(sale)
        coll_sale.insert(sale)
        if make_inventory_movement:
            _help_make_inventory_mov(remission)
        return {'remission': remission}
    elif required == 'serena/ticket':
        ticket = models.ticket.create()
        ticket.datetime = sale.datetime
        ticket.client = sale.client
        ticket.amount = sale.amount
        ticket['items'] = doc_items
        sale.document_sale = {'id': ticket['id'], 'type': ticket['type'], 'amount': ticket['amount']}
        ticket['sale'] = {'id': sale['id'], 'type': sale['type']}
        dictutils.dec_to_float(ticket)
        coll_ticket.replace_one({'id': ticket['id']}, ticket)
        dictutils.dec_to_float(sale)
        coll_sale.insert(sale)
        if make_inventory_movement:
            _help_make_inventory_mov(ticket)
        return {'ticket': ticket}
    elif required == 'serena/sale_note':
        sale_note = models.sale_note.create()
        sale_note['datetime'] = sale['datetime']
        sale_note['client'] = sale['client']
        sale_note['amount'] = sale['amount']
        sale_note['items'] = sale['items']
        sale_note['sale'] = {'id': sale['id'], 'type': sale['type']}
        sale['document_sale'] = {'id': sale_note['id'], 'type': sale_note['type']}
        dictutils.dec_to_float(sale_note)
        coll_sale_note.replace_one({'id': sale_note['id']}, sale_note)
        dictutils.dec_to_float(sale)
        if make_inventory_movement:
            _help_make_inventory_mov(sale_note)
        return {'sale_note': sale_note}


def __handle_action_serena_close_sale_ver_2(msg):
    try:
        sale = msg['sale']
        doc_items = list()
        for item in sale['items']:
            if 'selected_with' in item:
                del item['selected_with']
            doc_item = dict()
            doc_item['sku'] = item['sku']
            doc_item['quanty'] = item['quanty']
            doc_item['description'] = item['description']
            doc_item['price'] = item['price']['value']
            doc_item['amount'] = item['quanty'] * item['price']['value']
            doc_items.append(doc_item)
    
        if 'id' not in sale:
            sale['id'] = anelys.get_id_with_name('serena/sale')
    
        if 'type' not in sale:
            sale['type'] = 'serena/sale'
        elif 'type' in sale and sale.type != 'serena/sale':
            sale.purchase_price = sale.type
            sale.type = 'serena/sale'
    
        if 'datetime' not in sale and 'datetime' in msg:
            sale.datetime = msg.datetime
        elif 'datetime' not in sale and 'datetime' not in msg:
            sale['datetime'] = datetime_isoformat(datetime.now())
    
        if 'document_sale_required' in msg:
            required = msg['document_sale_required']
        else:
            required = 'serena/ticket'
    
        if required == 'serena/ticket':
            document = models.ticket.create()
        elif required == 'serena/sale_note':
            document = models.sale_note.create()
        else:
            document = models.ticket.create()
    
        document['amount'] = sale['amount']

        if 'client' in sale:
            client = sale['client']
            for k in list(client.keys()):
                if k not in ['id', 'type', 'name',]:
                    del client[k]

            document['client'] = client

        if 'datetime' in msg:
            document['datetime'] = msg['datetime']
        elif 'datetime' in sale:
            document['datetime'] = sale['datetime']
        else:
            document['datetime'] = datetime_isoformat(datetime.now())
        document['items'] = doc_items
        document['sale'] = {'id': sale['id'], 'type': sale['type']}
        sale.document = {'id': document.id, 'type': document.type}
    
        if 'make_inventory_movement' in msg and msg['make_inventory_movement']:
            from valentine.remote import make_movement
            make_movement(items=document['items'], storage=None, type='out',
                          origen={'id': document.id, 'type': document.type})
    
        dictutils.dec_to_float(document)
        if document['type'] == 'serena/ticket':
            coll_ticket.replace_one({'id': document['id']}, document, upsert=True)
        elif document['type'] == 'serena/sale_note':
            coll_sale_note.replace_one({'id': document['id']}, document, upsert=True)
        dictutils.float_to_dec(document)
    
        if '_id' in document:
            del document['_id']
    
        if 'order' in sale:
            order = sale['order']
            events.order_sold(order={'id': order.id, 'type': order.type}, sale={'id': sale.id, 'type': sale.type})
        elif 'orders' in sale:
            orders = [{'id': order.id, 'type': order.type} for order in sale.orders]
            events.order_sold(orders=orders, sale={'id': sale.id, 'type': sale.type})
    
        dictutils.dec_to_float(sale)
        coll_sale.update({'id': sale['id']}, sale, upsert=True)
        events.sale_closed(sale)
        return {'document': document, 'sale': sale}
    except Exception as e:
        print(e)


def handle_action_serena_create_product_set(msg):
    product_set = msg['product_set']
    product_set['type'] = 'serena/product_set'
    if 'id' not in product_set:
        product_set['id'] = anelys.get_id_with_name(product_set['type'])
    coll_product_set.insert(product_set)
    return {'product_set': product_set}


def handle_action_serena_set_payment(msg):

    def __help(dd):
        document = dd['document']
        if 'payment' in dd:
            map_collection[document.type].update_one({'id': document.id}, {'$set': {'payment': dd['payment']}})
        elif 'payments' in dd:
            map_collection[document.type].update_one({'id': document.id}, {'$set': {'payments': dd.payments}})
    if 'document' in msg:
        __help(msg)
    elif 'list' in msg:
        for ll in msg['list']:
            __help(ll)


def handle_action_serena_update_product_set(msg):
    pass


def handle_action_serena_close_sale(msg):
    if 'v' not in msg:
        return __handle_action_serena_close_sale_ver_1(msg)
    else:
        return __handle_action_serena_close_sale_ver_2(msg)


def handle_action_serena_order_change_status(msg):
    coll_order.update_one({'id': msg['order']['id'], 'status': msg['order']['status']},
                          {'$set': {'status': msg['status']}})
    msgevent = {'type_message': 'event', 'event': 'serena/order/update',
                'order': msg['order'], 'updated': {'status': msg['status']}}
    agent_ella.send_msg(msgevent)


def handle_action_serena_send_order(msg):
    order = msg['order']
    if 'id' not in order:
        order['id'] = anelys.get_id_with_name('serena/order')
    if 'type' not in order:
        order['type'] = 'serena/order'
    order['status'] = 'for_sort'
    coll_order.insert(order)
    del order['_id']
    msg = {'type_message': 'propagate_event', 'event': 'serena/order/received', 'order': order}
    agent_ella.send_msg(msg)


def handle_event_callie_command_to_sort_given(msg):
    cmdtosort = msg['command_to_sort']
    if isinstance(cmdtosort['to_sort'], str):
        coll_order.update_one({'id': cmdtosort['to_sort']}, {'$set': {'status': 'sorting'}})
    elif isinstance(cmdtosort['to_sort'], dict) and cmdtosort['to_sort']['type'] == 'serena/order':
        coll_order.update_one({'id': cmdtosort['to_sort']['id']}, {'$set': {'status': 'sorting'}})


def handle_event_serena_order_sold(msg):
    sale = msg['sale']

    def _helper(order):
        coll_order.update({'id': order['id']}, {'$set': {'status': 'sold', 'sale': sale}})
        msgevent = {'type_message': 'event', 'event': 'serena/order/updated', 'order': order,
                    'updated': {'status': 'sold'}}
        agent_ella.send_msg(msgevent)
    if 'order' in msg:
        _helper(msg['order'])
    elif 'orders' in msg:
        for pedido in msg['orders']:
            _helper(pedido)


def handle_event_callie_command_to_sort_sorted(msg):
    cmdtosort = msg['cmd_to_sort']

    def _helper(order_id):
        order = coll_order.find_one({'id': order_id})
        order['status'] = 'sorted'
        for itemsorted in cmdtosort['items']:
            if 'no_stocked' in itemsorted:
                for order_item in order['items']:
                    if order_item['sku'] == itemsorted['sku']:
                        order_item['no_stocked'] = itemsorted['no_stocked']
                        break
        coll_order.replace_one({'id': order['id']}, order)
        msgevent = {'type_message': 'event', 'event': 'serena/order/updated', 'order': order,
                    'updated': {'status': 'sorted'}}
        agent_ella.send_msg(msgevent)
    if isinstance(cmdtosort['to_sort'], str):
        _helper(cmdtosort['id'])
    elif isinstance(cmdtosort['to_sort'], dict) and cmdtosort['to_sort']['type'] == 'serena/order':
        _helper(cmdtosort['to_sort']['id'])


def handle_find_serena_order(msg):
    l_filt = dict()
    for k1, v1 in msg['query'].items():
        if k1 == 'status':
            if isinstance(v1, str):
                l_filt['status'] = v1
            elif isinstance(v1, dict):
                for k2, v2 in v1.items():
                    if k2 == '!in':
                        l_filt['stauts'] = {'$in': v2}
    result = list()
    c1 = coll_order.find(l_filt, {'_id': False})
    for doc in c1:
        result.append(doc)
    return {'result': result}


def handle_find_serena_product(msg):
    query = msg.query
    filt = dict()
    for k1, v1 in query.items():
        if k1 == 'description':
            if isinstance(v1, dict):
                for k2, v2 in v1.items():
                    if k2 == '!like':
                        filt.description = re.compile('.*' + re.escape(v2).replace('\\ ', '.*') + '.*', re.I)
    result = [product for product in coll_product.find(filt, {'_id': False})]
    if 'store' in query:
        store = query.store
        d5_session = d5.session()
        rr = d5_session.run('match (store{id:{store}.id})-[:not_sells]->(item)  '
                            'where item.sku in {items_sku} '
                            'return item.sku as sku;', {'store': store, 'items_sku': [item.sku for item in result]})
        items_sku = [rc['sku'] for rc in rr if rc['sku'] is not None]
        d5_session.close()
        result = [item for item in result if item.sku not in items_sku]

    if 'sort' in msg and isinstance(msg.sort, bool) and msg.sort:
        from itzamara import key_to_sort_item
        result.sort(key=key_to_sort_item)

    if 'limit' in msg and len(result) > msg.limit:
        result = result[:msg.limit]
    return {'result': result}


def handle_find_serena_product_set(msg):
    result = list(coll_product_set.find({}, {'_id': False}))
    return {'result': result}


def handle_find_store(msg):
    filter = Filter_Mongo()
    filter.fields = ['name', 'id', 'address.id']
    filter.parse_anelys_query(msg.query)
    result = coll_store.find(filter.dict, {'_id': False})
    return {'result': result}


def handle_find_one_serena_order(msg):
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filter['id'] = v1
    result = coll_order.find_one(l_filter, {'_id': False})
    return {'result': result}


def handle_find_one_serena_product(msg):
    withprice = True
    if 'projection' in msg:
        if 'price' not in msg.projection:
            withprice = False
        else:
            withprice = msg.projection.price
    product = d1.serena.product.find_one({'sku': msg.query.sku}, {'_id': False})
    product['type'] = 'serena/product'

    if product is not None and 'store' in msg.query and 'id' in msg.query.store and msg.query.store.id is not None:
        store_id = msg.query.store.id
        d5_session = d5.session()
        res = d5_session.run('MERGE (store{id:{store_id}}) '
                             'MATCH (product{sku:{product_sku}}) where not ((store)-[:not_sells]->(product) '
                             'return count(product) as count;',
                             {'store_id': store_id, 'product_sku': product.sku})
        count = res.single()['count']
        if count == 0:
            product = None
        d5_session.close()

    if withprice and product is not None:
        getprice = {'type_message': 'find_one', 'type': 'perla/price', 'query': {'sku': product['sku']}}
        if 'wholesale' in msg['query']:
            getprice['query']['wholesale'] = msg['query']['wholesale']
        elif 'client' in msg['query'] and 'wholesale' in msg['query']['client']:
            getprice['query']['wholesale'] = msg['quiery']['client']['wholesale']
        answer = agent_perla.send_msg(getprice)
        product['price'] = answer['result']
    return {'result': product}


def handle_find_one_serena_product_set(msg):
    l_filt = dict()
    if 'query' in msg:
        for v1, k1 in msg['query'].items():
            if v1 == 'skus':
                if isinstance(k1, dict):
                    for k2, v2 in k1.items():
                        if k2 == '!contains':
                            if isinstance(v2, dict):
                                for k3, v3 in v2.items():
                                    if k3 == 'sku':
                                        l_filt['skus'] = {'$in': [v3]}
    return {'result': coll_product_set.find_one(l_filt, {'_id': False})}


def handle_find_one_store(msg):
    filter = Filter_Mongo()
    filter.fields.extend(['id'])
    filter.parse_anelys_query(msg.query)
    return {'result': coll_store.find_one(filter.dict, {'_id': False})}


def handle_get_domains_serena_store(msg):
    return {'store': local_store}


read_msg = Pool_Handler()
rr = read_msg
rr['type_message=action.action=serena/close_sale'] = handle_action_serena_close_sale
rr['type_message=action.action=serena/create_product_set'] = handle_action_serena_create_product_set
rr['type_message=action.action=serena/order/change_status'] = handle_action_serena_order_change_status
rr['type_message=action.action=serena/send_order'] = handle_action_serena_send_order
rr['type_message=action.action=serena/set_payment'] = handle_action_serena_set_payment
rr['type_message=event.event=callie/command_to_sort/given'] = handle_event_callie_command_to_sort_given
rr['type_message=event.event=callie/command_to_sort/sorted'] = handle_event_callie_command_to_sort_sorted
rr['type_message=event_notification.event=callie/command_to_sort/given'] = handle_event_callie_command_to_sort_given
rr['type_message=event_notification.event=callie/command_to_sort/sorted'] = handle_event_callie_command_to_sort_sorted
rr['type_message=find.type=serena/order'] = handle_find_serena_order
rr['type_message=find.type=serena/product'] = handle_find_serena_product
rr['type_message=find.type=serena/product_set'] = handle_find_serena_product_set
rr['type_message=find.type=serena/store'] = handle_find_store
rr['type_message=find_one.type=serena/order'] = handle_find_one_serena_order
rr['type_message=find_one.type=serena/product'] = handle_find_one_serena_product
rr['type_message=find_one.type=serena/product_set'] = handle_find_one_serena_product_set
rr['type_message=find_one.type=serena/store'] = handle_find_one_store
rr['type_message=request.request_type=get.get=serena/domains_serena_store'] = handle_get_domains_serena_store

if __name__ == '__main__':
    print("I'm serena.")
    recipient = Recipient()
    recipient.prepare('/serena', read_msg)
    recipient.begin_receive_forever()
