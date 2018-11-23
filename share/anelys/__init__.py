from katherine import citlali_maria


def get_id_with_prefix(prefix):
    citlali_maria.ping(True)
    cursor = citlali_maria.cursor()
    cursor.execute('SELECT serie FROM anelys.prefix_serie WHERE prefix = %s LIMIT 1;', (prefix,))
    if cursor.rowcount == 1:
        serie, = cursor.fetchone()
        id = prefix + '-' + str(serie)
        cursor.execute('UPDATE anelys.prefix_serie SET serie = serie + 1 WHERE prefix = %s;', (prefix,))
    else:
        cursor.execute('INSERT anelys.prefix_serie (prefix, serie) VALUES (%s, 2);', (prefix,))
        id = prefix + '-1'
    cursor.close()
    return id


def get_id_with_name(name):
    citlali_maria.ping(True)
    cursor = citlali_maria.cursor()
    cursor.execute('select prefix from anelys.type_prefix WHERE name = %s limit 1;', (name,))

    if cursor.rowcount == 1:
        prefix, = cursor.fetchone()
        id = get_id_with_prefix(prefix)
    else:
        id = get_id_with_prefix(name.replace('/', '_'))
    cursor.close()
    return id

get_id = get_id_with_name


class model():
    @staticmethod
    def create():
        return