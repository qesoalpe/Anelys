from pathlib import Path
from dict import Dict as dict, List as list
from utils import count_lines, checksum_md5
from isodate import datetime_isoformat
from datetime import datetime
from pymongo import MongoClient
from pprint import pprint
import json


d1 = MongoClient(document_class=dict)

root_anelys_python = Path('C:/home/picazo/anelys/python')

share = root_anelys_python / Path('share')
alfa = root_anelys_python / Path('alfa')
isis = root_anelys_python / Path('isis')


def dir_is_allowed(pathdir):
    return not (pathdir.name.startswith('.') or pathdir.name.startswith('__'))


def list_dir(path):
    r = list()
    for pathchild in path.iterdir():
        if pathchild.is_file() or (pathchild.is_dir() and dir_is_allowed(pathchild)):
            r.append(pathchild)
            if pathchild.is_dir():
                r.extend(list_dir(pathchild))
    return r


share = dict({'path': share})

share.children = list({'path': p.relative_to(share.path), 'absolutpath': p} for p in list_dir(share.path) if not p.is_dir())

print(len(share.children))
print(len([x for x in share.children if 'absolutpath' in x]))
print(len([x for x in share.children if 'absolutpath' not in x]))

pprint(share)
c = 0
for child in share.children:
    try:
        if child.absolutpath.is_file():
            child.md5 = checksum_md5(child.absolutpath)
            stat = child.absolutpath.stat()
            child.size = stat.st_size
            child.modified = datetime_isoformat(datetime.fromtimestamp(stat.st_mtime))

        child.path = child.path.as_posix()
        del child.absolutpath
        c += 1
    except Exception as e:
        print(child)
        print(share.children.index(child))
        print(c)
        raise e


f = open('/home/picazo/package.share.json', 'wt', encoding='utf8')
json.dump(share.children, f, ensure_ascii=False, indent=2)
f.close()
