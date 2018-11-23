from katherine import d1
from anelys import get_id_with_name

coll_item_list = d1.itzamara.item_list


def handle_action_itzamara_save_item_list(msg):
    itemlist = msg['item_list']
    if 'type' not in itemlist:
        itemlist.type = 'itzamara/item¿'
    if 'id' not in itemlist:
        itemlist.id = get_id_with_name(itemlist.type)
    if 'update' not in itemlist:
        coll_item_list.replace_one({'id': itemlist['id']}, itemlist, upsert=True)
    return {'item_list': itemlist}


def map_functions(rr):
    rr['type_message=action.action=itzamara/create_item_list'] = handle_action_itzamara_save_item_list
    rr['type_message=action.action=itzamara/update_item_list'] =  handle_action_itzamara_save_item_list
    rr['type_message=action.action=itzamara/save_item_list'] = handle_action_itzamara_save_item_list