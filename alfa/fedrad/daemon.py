from sarah.acp_bson import Recipient
from math import ceil, floor
from katherine import d1
import fedra

db_fedra = d1.fedra

coll_file = db_fedra.get_collection('file')
coll_directory = db_fedra.get_collection('directory')
coll_drive = db_fedra.get_collection('drive')
coll_chunk = db_fedra.get_collection('chunk')
coll_chunker = db_fedra.get_collection('chunker')

FILE_LENGTH_LIMIT = 67108864


def list_directory(directory):
    result = list()
    for rr in coll_file.find({'directory': directory}, {'_id': False}):
        result.append(rr)

    for rr in coll_directory.find({'parent': directory}, {'_id': False}):
        result.append(rr)

    from sorter import Sorter
    sorter = Sorter()
    sorter.columns.add('name', Sorter.ASC)
    sorter.sort(result)
    return result


def is_directory(path, drive, cursor):
    if path[-1:] == '/':
        del path[-1:]
    if isinstance(drive, dict) and 'id' in drive:
        drive = drive['id']
    cursor.execute('SELECT type FROM fedra.path WHERE path = %s AND drive_id = %s LIMIT 1;', (path, drive))
    if cursor.rowcount == 1:
        l_type, = cursor.fetchone()
        if l_type == 'fedra/directory':
            return True
    return False


def move(drive, source, dest=None, directory=None):
    if isinstance(source, str) and (isinstance(dest, str) or isinstance(directory, str)):
        ff = coll_file.find_one({'path': source, 'drive.id': drive['id']})
        if ff is not None:
            if dest is not None:
                ffdest = coll_file.find_one({'path': dest, 'drive.id': drive['id']}, {'id': True, '_id': False})
                if ffdest is not None:
                    return {'error': True, 'error_msg': 'ya existe un file con el nombre'}
                if dest[-1:] == '/':
                    del dest[-1:]
                ffdest = coll_directory.find_one({'drive.id': drive['id'], 'path': dest})
                if ffdest is not None:
                    ff['path'] = dest + '/' + ff['name']
                    ff['directory'] = {'id': ffdest['id'], 'type': ffdest['type']}
                    return
                dest += '/'
                ffdest = coll_directory.find_one({'drive.id': drive['id'], 'path': dest})
                if ffdest is not None:
                    ff['path'] = dest + ff['name']
                    ff['directory'] = {'id': ffdest['id'], 'type': ffdest['type']}
                    return
            elif directory is not None:
                pass
        else:
            if source[-1:] == '/':
                del source[-1:]
            ff = coll_directory.find_one({'path': source, 'drive.id': drive['id']})
    elif source['type'] == 'fedra/file':
        if directory is not None and 'path' in directory and 'id' in directory:
            dest_path = directory['path']
            if dest_path[-1:] != '/':
                dest_path += '/'
            source['path'] = dest_path + source['name']
            source['directory'] = {'id': directory['id'], 'type': directory['type']}
            coll_file.replace_one({'id': source['id'], 'drive.id': drive['id']}, source)
    elif source['type'] == 'fedra/directory':
        pass


def handle_get_fedra_file(msg):
    l_filter = dict()
    query = msg['query']
    if 'file' in query and 'id' in query['file']:
        l_filter['file.id'] = query['file']['id']
    elif 'id' in query:
        l_filter['file.id'] = query['id']
    elif 'path' in query:
        l_filter['path'] = query['path']

    file = coll_file.find({'id': msg['file']['id']}, {'_id': False, 'directory': False, 'upload_datetime': False,
                                                      'path': False, 'chunk_size': False})
    file_length = file['length']
    if file_length > FILE_LENGTH_LIMIT:
        return {'error': True, 'error_msg': 'file exced the length limit allowed'}
    data = bytearray(file_length)
    count = 0
    for chunk in coll_chunk.find({'file.id': file['id']}).sort('n', 1):
        data[count:len(chunk['data'])-1] = chunk['data']
        count += len(chunk['data'])
    file['data'] = bytes(data)
    return {'file': data}


def handle_get_fedra_list_directory_contents(msg):
    mariadb_conn = mariadb.connect(**config['mariadb'])
    cursor = mariadb_conn.cursor()
    dir_path = None
    drive_id = None
    if 'directory' in msg and isinstance(msg['directory'], dict):
        directory = msg['directory']
        if 'path' in directory:
            dir_path = directory['path']
        else:
            dd = coll_directory.find_one({'id': directory['id']}, {'_id': False, 'path': True})
            dir_path = dd['path']
    elif 'path' in msg:
        dir_path = msg['path']
    if 'drive' in msg and 'id' in msg['drive']:
        drive_id = msg['drive']['id']
    if dir_path[-1] == '/' and len(dir_path) > 1:
        del dir_path[-1]
    assert isinstance(dir_path, str)
    list_directory = list()
    cursor.execute(r"SELECT path.name COLLATE 'utf8_general_ci', path.type COLLATE 'utf8_general_ci', file.length FROM "
                   r"fedra.path LEFT JOIN fedra.file ON file.id = path.id WHERE path.parent = %s AND "
                   r"path.drive_id = %s;", (dir_path, drive_id))
    for name, l_type, length in cursor:
        item = {'type': l_type}
        if name is not None:
            item['name'] = name
        if length is not None:
            item['length'] = length
        list_directory.append(item)
    mariadb_conn.close()
    return {'list': list_directory}


def handle_get_fedra_next_chunk(msg):
    chunker = coll_chunker.find_one({'id': msg['chunker']['id']})
    if chunker is None:
        return {'data': None}
    file = chunker['file']
    chunk_size = chunker['chunk_size']
    offset = chunker['offset']

    if offset + chunk_size > file['length']:
        data = bytearray(file['length'] - offset)
    else:
        data = bytearray(chunk_size)
    min_chunk_n = floor(offset / file['chunk_size'])
    chunk_offset = offset % file['chunk_size']
    max_chunk_n = ceil((chunk_offset + len(data)) / file['chunk_size']) + min_chunk_n
    l_filter = {'file.id': file['id'], '$and': [{'n': {'$gte': min_chunk_n}}, {'n': {'$lt': max_chunk_n}}]}
    data_offset = 0
    data_left = len(data)
    to_transfer = file['chunk_size'] - chunk_offset
    for chunk in coll_chunk.find(l_filter).sort('n', 1):
        data[data_offset:data_offset+to_transfer] = chunk['data'][chunk_offset:to_transfer+chunk_offset]
        data_offset += file['chunk_size']
        data_left -= to_transfer
        if data_left < file['chunk_size']:
            to_transfer = data_left
        else:
            to_transfer = file['chunk_size']
        chunk_offset = 0
    chunker['offset'] += len(data)
    if chunker['offset'] == file['length']:
        coll_chunker.remove({'id': chunker['id']})
    else:
        coll_chunker.replace_one({'id': chunker['id']}, chunker)
    return {'data': data}


def handle_put_fedra_file(msg):
    pass


if __name__ == '__main__':
    recipient = Recipient()
    recipient.prepare('/fedra')
    recipient.reg('type_message=action.action=put.put=fedra/file', handle_put_fedra_file)
    recipient.reg('type_message=find_one.type=fedra/file', handle_get_fedra_file)
    recipient.reg('type_message=request.request_type=get.get=fedra/list_directory',
                  handle_get_fedra_list_directory_contents)
    recipient.reg('type_message=request.request_type=get.get=fedra/file', handle_get_fedra_file)
    recipient.reg('type_message=request.request_type=put.put=fedra/file', handle_put_fedra_file)
    print('I\'m fedra.')
    recipient.begin_receive_forever()
