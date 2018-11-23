from katherine import d1, d6
from dict import Dict as dict
assert dict is d1.codec_options.document_class
db_serena = d1.get_database('serena')

coll_ticket = db_serena.get_collection('ticket')
coll_document_cost = d1.valentine.document_cost
coll_sale_cost = d1.valentine.sale_cost
coll_document_removed = db_serena.get_collection('document_removed')
coll_sale_removed = d1.serena.sale_removed
coll_sale = db_serena.get_collection('sale')
db_valentine = d1.get_database('valentine')
coll_vasya_transaction = db_valentine.get_collection('transaction')
db_vasya = d1.get_database('vasya')
coll_valentine_transaction = db_vasya.get_collection('transaction')


def remove_ticket(ticket_id):
    d6.ping(True)
    maria_cursor = d6.cursor()
    ticket = coll_ticket.find_one({'id': ticket_id})
    coll_document_removed.insert_one(ticket)
    coll_ticket.remove({'id': ticket.id})

    if 'sale' in ticket:
        sale = coll_sale.find_one({'id': ticket.sale.id})
        if sale is not None:
            coll_sale.remove({'id': sale.id})
            coll_sale_removed.insert_one(sale)
        coll_sale_cost.remove({'id': ticket.sale.id})

    if 'payment' in ticket and ticket.payment.type == 'vasya/transaction':
        coll_vasya_transaction.remove({'id': ticket.payment.id})
        maria_cursor.execute('DELETE from vasya.transaction WHERE id = %s;', (ticket.payment.id,))

    maria_cursor.execute('DELETE FROM valentine.transaction WHERE origen_id = %s', (ticket.id,))
    coll_valentine_transaction.remove({'origen.id': ticket.id})
    maria_cursor.close()
    print('removed')


if __name__ == '__main__':
    ll = []
    for l in ll:
        remove_ticket(l)
