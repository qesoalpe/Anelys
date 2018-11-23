def find_one(function, iterable):
    for item in iterable:
        if function(item):
            return item
    else:
        return None


def remove_values_none(dict):
    for k in list(dict.keys()):
        if dict[k] is None:
            del dict[k]


def isnumeric(value):
    from decimal import Decimal
    try:
        i = Decimal(value)
        return True
    except:
        return False


is_numeric = isnumeric


def count_lines(filepath):
    from itertools import takewhile, repeat
    f = open(filepath, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024 * 1024) for _ in repeat(None)))
    return sum(buf.count(b'\n') for buf in bufgen)


def checksum_md5(filepath):
    import hashlib
    md5 = hashlib.md5()
    blocksize = 1024 * 1024 * 5  # 10 MiB
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            md5.update(block)
    return md5.hexdigest().upper()
