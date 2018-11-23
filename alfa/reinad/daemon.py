from sarah.acp_bson import Recipient, Pool_Handler
import re
from anelys import get_id_with_name
from katherine import d1

db_reina = d1.reina
coll_entity = db_reina.get_collection('entity')
coll_corporation = db_reina.get_collection('corporation')
coll_person = db_reina.get_collection('person')


def create_entity_from_sub(subentity):
    entity = {'id': subentity['id'], 'type': 'reina/entity', 'entity_type': subentity['type']}
    if 'business_name' in subentity:
        entity['name'] = subentity['business_name']
    elif 'name' in subentity:
        entity['name'] = subentity['name']
    coll_entity.insert(entity)


def update_entity_from_sub(subentity):
    entity = {'id': subentity['id'], 'type': 'reina/entity', 'entity_type': subentity['type']}
    if 'business_name' in subentity:
        entity['name'] = subentity['business_name']
    elif 'name' in subentity:
        entity['name'] = subentity['name']
    coll_entity.replace_one({'id': entity['id']}, entity)


def get_person_name(person):
    names = list()
    if 'given_name' in person:
        person.given_name = person['given_name'].strip()
        names.append(person['given_name'])
    if 'middle_name' in person:
        person.middle_name = person.middle_name.strip()
        names.append(person['middle_name'])
    if 'paternal_surname' in person:
        person.paternal_surname = person['paternal_surname'].strip()
        names.append(person['paternal_surname'])
    if 'maternal_surname' in person:
        names.append(person['maternal_surname'])
    return ' '.join(names)

# -->


def handle_action_reina_create_person(msg):
    person = msg['person']
    if 'type' not in person:
        person.type = 'reina/person'
    if 'id' not in person:
        person.id = get_id_with_name('reina/person')
    person['name'] = get_person_name(person)
    coll_person.insert_one(person)
    del person['_id']
    # create_entity_from_sub(person)
    return {'person': person}


def handle_action_reina_create_corporation(msg):
    corp = msg['corporation']
    if 'type' not in corp:
        corp.type = 'reina/corporation'
    if 'id' in corp:
        corp.id = get_id_with_name(corp.type)
    coll_corporation.insert(corp)
    del corp['_id']
    # create_entity_from_sub(corp)
    return {'corporation': corp}


def handle_action_reina_update_corporation(msg):
    if 'corporation' in msg:
        corp = msg['corporation']
        coll_corporation.replace_one({'id': corp['id']}, corp)
        del corp['_id']
        update_entity_from_sub(corp)


def handle_action_reina_update_person(msg):
    if 'person' in msg:
        person = msg['person']
        person['name'] = get_person_name(person)
        update_entity_from_sub(person)
        coll_person.replace_one({'id': person['id']}, person)


def handle_find_reina_corporation(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            l_filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.IGNORECASE)
    result = list()
    for doc in coll_corporation.find(l_filt, {'_id': False}):
        result.append(doc)
    return {'result': result}


def handle_find_reina_entity(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            l_filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.IGNORECASE)
    result = list()
    for doc in coll_entity.find(l_filt, {'_id': False}):
        result.append(doc)
    return {'result': result}


def handle_find_reina_person(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'name':
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 == '!like':
                            l_filt['name'] = re.compile('.*' + v2.replace(' ', '.*') + '.*', re.IGNORECASE)
    result = list()
    for doc in coll_person.find(l_filt, {'_id': False}):
        result.append(doc)
    return {'result': result}


def handle_find_one_reina_corporation(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filt['id'] = v1
    return {'result': coll_corporation.find_one(l_filt, {'_id': False})}


def handle_find_one_reina_entity(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filt['id'] = v1
    result = coll_corporation.find_one(l_filt, {'_id': False})
    if result is not None:
        return {'result': result}
    result = coll_person.find_one(l_filt, {'_id': False})
    return {'result': result}


def handle_find_one_reina_person(msg):
    l_filt = dict()
    if 'query' in msg and isinstance(msg['query'], dict):
        for k1, v1 in msg['query'].items():
            if k1 == 'id':
                l_filt['id'] = v1
    return {'result': coll_person.find_one(l_filt, {'_id': False})}


handler_msg = Pool_Handler()
hh = handler_msg
hh.reg('type_message=action.action=reina/create_corporation', handle_action_reina_create_corporation)
hh.reg('type_message=action.action=reina/create_person', handle_action_reina_create_person)
hh.reg('type_message=action.action=reina/register_corporation', handle_action_reina_create_corporation)
hh.reg('type_message=action.action=reina/register_person', handle_action_reina_create_person)
hh.reg('type_message=action.action=reina/update_corporation', handle_action_reina_update_corporation)
hh.reg('type_message=action.action=reina/update_person', handle_action_reina_update_person)
hh.reg('type_message=find.type=reina/corporation', handle_find_reina_corporation)
hh.reg('type_message=find.type=reina/entity', handle_find_reina_entity)
hh.reg('type_message=find.type=reina/person', handle_find_reina_person)
hh.reg('type_message=find_one.type=reina/corporation', handle_find_one_reina_corporation)
hh.reg('type_message=find_one.type=reina/entity', handle_find_one_reina_entity)
hh.reg('type_message=find_one.type=reina/person', handle_find_one_reina_person)

if __name__ == '__main__':
    print("I'm reina.")
    recipient = Recipient()
    recipient.prepare('/reina', handler_msg)
    recipient.begin_receive_forever()
