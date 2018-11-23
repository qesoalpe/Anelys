from sarah.acp_bson import Pool_Handler, Recipient, Client
from anelys import get_id_with_name
from isodate import datetime_isoformat
from datetime import datetime
from sarah import dictutils
from katherine import d1

db_donell = d1.get_database('donell')

coll_production = db_donell.get_collection('production')

agent_valentine = Client('donell', 'valentine')


def handle_action_donell_create_production(msg):
    production = msg['production']
    if 'type' not in production:
        production['type'] = 'donell/production'
    if 'id' not in production:
        production['id'] = get_id_with_name(production['type'])

    if 'datetime' not in production:
        if 'datetime' in msg:
            production['datetime'] = msg['production']
        else:
            production['datetime'] = datetime_isoformat(datetime.now())
    storage = production['storage']
    consumed = production['consumed']
    produced = production['produced']
    msg = {'type_message': 'action', 'action': 'valentine/make_movement', 'storage': storage, 'mov_type': 'out',
           'items': consumed, 'origen': {'id': production['id'], 'type': production['type']}}

    agent_valentine(msg)

    msg['mov_type'] = 'in'
    msg['items'] = produced

    agent_valentine(msg)
    dictutils.dec_to_float(production)
    coll_production.insert(production)
    if '_id' in production:
        del production['_id']
    return {'production': production}


rr = Pool_Handler()
rr.reg('type_message=action.action=donell/create_production', handle_action_donell_create_production)

if __name__ == '__main__':
    print('I\'m donell')
    recipient = Recipient()
    recipient.prepare('donell', rr)
    recipient.begin_receive_forever()
