from katherine import citlali_maria


mariadb_config = {'host': '127.0.0.1', 'port': 8801,
                  'user': 'citlali', 'passwd': 'que_cantann',
                  'autocommit': True, 'charset': 'utf8'}


def get_address_port_recipient(recipient_id, dictionary=None):
    citlali_maria.ping(True)
    c1 = citlali_maria.cursor()
    c1.execute('SELECT address, port FROM mary.end_point_recipient WHERE recipient_id = %s', (recipient_id,))
    if c1.rowcount == 1:
        address_port = c1.fetchone()
    else:
        raise Exception('recipient_id %s was not found' % recipient_id)
    c1.close()
    return address_port
