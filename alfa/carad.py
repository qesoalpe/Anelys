from pymongo import MongoClient
from dict import Dict


d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)

d1.admin.authenticate('alejandro', '47exI4')

coll_task = d1.get_database('cara').get_collection('task')

cursor = coll_task.find({}, {'_id': False})
tasks = [task for task in cursor]


