from pymongo import MongoClient
import os
import mimetypes
from sarah.acp_bson import Client


d8757_11 = MongoClient('mongodb://comercialpicazo.com:27030')
d8757_11.admin.authenticate('alejandro', '47exI4')
agent_anelys = Client('fedra.save', 'anelys')

DEFAULT_CHUNK_SIZE = 1024 * 255 # 255KiB

def save_file(filename):
    if not os.path.exists(filename):
        return False
    f = open(filename, 'rb')
    
    chunk_size = DEFAULT_CHUNK_SIZE
    file = {'length': os.path.getsize(filename), 'chunk_size': chunk_size, 'filename': os.path.basename(f.name), 'type': 'fedra/file'}
    mime_type = mimetypes.guess_type(f.name)
    if mime_type[0] is not None:
        file['mime_type'] = mime_type[0]
    answer = agent_anelys({'type_message': 'request', 'request_type': 'get', 'get': 'anelys/get_id_with_name', 'name': file['type']})
    file['id'] = answer['id']
    chunks, remain = divmod(file['length'], chunk_size)
    
    d8757_11.fedra.file.insert(file)
    chunk_n = 0
    uploaded = 0
    while uploaded < file['length']:
        chunk = {'data_model': f.read(chunk_size), 'file': {'id': file['id'], 'type': file['type']}, 'n': chunk_n}
        d8757_11.fedra.chunk.insert(chunk)
        chunk_n += 1
        uploaded += len(chunk['data_model'])
    return True

