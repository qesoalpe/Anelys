from katherine import d1
import anelys
from dict import Dict
db = d1.serena
coll_remission = db.get_collection('remission')
coll_sale_note = db.get_collection('sale_note')
coll_ticket = db.get_collection('ticket')


class remission:
    type = 'serena/remission'

    @classmethod
    def create(cls):
        remission = Dict({'id': anelys.get_id_with_name(cls.type), 'type': cls.type})
        coll_remission.insert_one(remission)
        del remission['_id']
        return remission


class sale_note:
    type = 'serena/sale_note'

    @classmethod
    def create(cls):
        sale_note = Dict({'id': anelys.get_id_with_name(cls.type), 'type': cls.type})
        coll_sale_note.insert(sale_note)
        del sale_note['_id']
        return sale_note


class ticket:
    type = 'serena/ticket'

    @classmethod
    def create(cls):
        ticket = Dict({'id': anelys.get_id_with_name(cls.type), 'type': cls.type})
        coll_ticket.insert_one(ticket)
        del ticket['_id']
        return ticket
