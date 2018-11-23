from sarah.acp_bson import Recipient
from anelys import get_id_with_name


def handle_get_anelys_get_with_name(msg):
    return {'id': get_id_with_name(msg.name)}


if __name__ == '__main__':
    from sarah.handler import Pool_Handler
    h = Pool_Handler()
    h['type_message=request.request_type=get.get=anelys/get_id_with_name'] = handle_get_anelys_get_with_name
    h['type_message=request.request_type=get.get=anelys/id_with_name'] = handle_get_anelys_get_with_name
    print('I\'m Anelys.')
    r = Recipient()
    r.prepare('anelys', h)
    r.begin_receive_forever()
