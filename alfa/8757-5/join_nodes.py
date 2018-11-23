from katherine import d5
import sys

id_old = -1
id_new = -1

if id_old == -1 or id_new == -1:
    sys.exit(0)

d5_session = d5.session()

# first ()-[rel]->(id_old)

rr = d5_session.run('match ()-[rel]->(old) where id(old) = {id} return distinct type(rel) as type;', {'id': id_old})

types = list()

for rec in rr:
    types.append(rec['type'])

for t in types:
    stmt = 'MATCH (item)-[rel:' + t + ']->(old) where id(old) = {id_old} ' \
           'MATCH (new) where id(new) = {id_new} ' \
           'CREATE UNIQUE (item)-[nrel:' + t + ']->(new) ' \
           'SET nrel += rel ' \
           'DELETE rel;'
    rr = d5_session.run(stmt, {'id_old': id_old, 'id_new': id_new, 'rel_type': t})
    rr.single()

rr = d5_session.run('match ()<-[rel]-(old) where id(old) = {id} return distinct type(rel) as type;', {'id': id_old})

types = list()

for rec in rr:
    types.append(rec['type'])

for t in types:
    stmt = 'MATCH (item)<-[rel:'+ t + ' ]-(old) where id(old) = {id_old} ' \
           'MATCH (new) where id(new) = {id_new} ' \
           'CREATE UNIQUE (item)<-[nrel:' + t + ']-(new) ' \
           'SET nrel += rel ' \
           'DELETE rel;'
    rr = d5_session.run(stmt, {'id_old': id_old, 'id_new': id_new})
    rr.single()
rr = d5_session.run('MATCH (old) where ID(old) = {id_old} return labels(old) as labels;', {'id_old': id_old})

labels = rr.single()['labels']

for label in labels:
    rr = d5_session.run('MATCH (p) where ID(p) = {id} SET p :' + label + '', {'id': id_new})
    rr.single()

rr = d5_session.run('MATCH (old) where ID(old) = {id_old} '
                    'MATCH (new) where ID(new) = {id_new} '
                    'SET new += old delete old;', {'id_old': id_old, 'id_new': id_new})
rr.single()

rr = d5_session.run('MATCH (old) where ID(old) = {id_old} delete old;', {'id_old': id_old})
rr.single()
d5_session.close()

print('ready')
