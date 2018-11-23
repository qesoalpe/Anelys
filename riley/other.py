from pprint import pprint
from pathlib import Path

exclude_dirname = ['.idea', '__pycache__']


def dir_is_admited(path):
    return not (path.name.startswith('.') or path.name.startswith('__'))


def count_lines(filepath):
    from itertools import takewhile, repeat
    f = open(filepath, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024 * 1024) for _ in repeat(None)))
    return sum(buf.count(b'\n') for buf in bufgen)


path_root = Path('/home/picazo/anelys/python')


def parse_dir(path):
    r = list()
    for pathchild in path.iterdir():
        if pathchild.is_file() or (pathchild.is_dir() and dir_is_admited(pathchild)):
            r.append(pathchild)
            if pathchild.is_dir():
                r.extend(parse_dir(pathchild))
    return r


paths = [p.relative_to(path_root) for p in parse_dir(path_root)]

paths.sort(key=lambda x: x)

pprint([str(path) for path in paths])
print('total paths:', len(paths))

python_files = list(filter(lambda x: (path_root / x).is_file() and x.suffix.lower() in ['.py', '.pyw'], paths))

print('python files:', len(python_files))

lines = sum([count_lines(path_root / fp) for fp in python_files])

print('lines:', lines)

print('directories:', len(list(filter(lambda x: (path_root / x).is_dir() and x.name not in ['__pycache__'], paths))))
