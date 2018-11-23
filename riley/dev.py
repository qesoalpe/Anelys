from dict import Dict as dict
import os
import os.path
from isodate import datetime_isoformat
from datetime import datetime
from pathlib import Path

path_root = Path(r'/home/picazo/anelys')

if os.path.sep != '/':
    os.path.sep = '/'

from katherine import d6


def get_datetime(timestamp):
    return datetime_isoformat(datetime.fromtimestamp(timestamp))


def parse_dir(dirpath):
    dir = Dict()
    dir.children = list()
    dir.path = '/' + dirpath + '/'
    dir.type = 'riley/directory'
    if path_relative:
        paths = os.listdir(dirpath)
        if dirpath != '.':
            paths = [os.path.join(dirpath, path).replace('\\', '/') for path in paths]
        else:
            paths = [path.replace('\\', '/') for path in paths]
        for path in paths:
            if os.path.isdir(path) and os.path.basename(path) not in ['__cache__', '__pycache__']:
                dir.children.append(parse_dir(path))
            elif os.path.isfile(path) and os.path.splitext(path)[1] in ['.py', '.pyw']:
                f = open(path, 'rb')
                import hashlib
                md5_hashlib = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hashlib.update(chunk)
                f.close()
                file = Dict()
                file.md5 = md5_hashlib.hexdigest().upper()
                file.path = '/' + path
                file.size = os.path.getsize(path)
                file.modified_datetime = get_datetime(os.path.getmtime(path))
                file.type = 'riley/file'
                dir.children.append(file)
    return dir

os.chdir(path_root)
tree = parse_dir('.')


def get_locals(dir):
    rr = [child for child in dir.children if child.type == 'riley/file']
    for m in [child for child in dir.children if child.type == 'riley/directory']:
        rr.extend(get_locals(m))
        from copy import deepcopy
        m = deepcopy(m)
        for k in list(m.keys()):
            if k not in ['path', 'type']:
                del m[k]
        rr.append(m)
    return rr


locals = get_locals(tree)

# cursor_db = db_mariadb.cursor()


# from pprint import pprint
#
# cursor_db = db_mariadb.cursor(pymysql.cursors.DictCursor)
# cursor_db.execute('select filepath as path, md5, size, modified_datetime from riley.file;')
#
# remotes = [Dict(file) for file in cursor_db]
#
# for file in remotes:
#     file.modified_datetime = datetime_isoformat(file.modified_datetime)
#
#

#
# for katherine in locals:
#     if 'path' in katherine:
#         if katherine.path[0] != '/':
#             katherine.path = '/' + katherine.path
#
# from pymongo import MongoClient
# db_mongo_local = MongoClient(port=27020)
# db_riley = db_mongo_local.get_database('riley')
# coll_snapshot_sync = db_riley.get_collection('snapshot_sync')
#
# snapshot = coll_snapshot_sync.find_one(projection={'_id': False},
#                                        sort=[('datetime', -1)])
# if snapshot is not None:
#     snapshots = snapshot.snapshots
# else:
#     snapshots = None
#
# persisted_path = [file.path for file in persisted]
# locals_path = [file.path for file in locals]
#
#
# def persist_file(file):
#     pass
#
# pprint(locals_path)
# pprint(persisted_path)
#
#
# snapshots = Dict({'snapshot': locals, 'datetime': datetime_isoformat(datetime.now())})