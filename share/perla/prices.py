import pymysql

from katherine import d6_config


def get_items_price_related(sku):
    d6 = pymysql.connect(**d6_config)
    d6_cursor = d6.cursor(cursor=pymysql.cursors.DictCursor)
    r = d6_cursor.execute('select distinct item.sku, item.description from itzamara.item where sku in '
                          '(select product_sku from perla.key_price where price_id in (select price_id from '
                          'perla.key_price where product_sku = %s))', (sku,))

    result = d6_cursor.fetchall()
    d6_cursor.close()
    d6.close()
    return result


def get_last_purchase_price(item, date=None, datetime=None):
    d6 = pymysql.connect(**d6_config)
    d6_cursor = d6.cursor()
    price = None
    if date is not None or datetime is not None:
        if date is not None:
            var = date
        else:
            var = datetime
        stmt = 'select price_value from perla.purchase_price where local_item_sku = %s and datetime <= %s ' \
               'order by datetime desc limit 1'
        r = d6_cursor.execute(stmt, (item.sku, var))
        if r == 1:
            price, = d6_cursor.fetchone()
        else:
            stmt = 'select price_value from perla.purchase_price where local_item_sku = %s and datetime >= %s ' \
                   'order by datetime asc limit 1'
            r = d6_cursor.execute(stmt, (item.sku, var))
            if r == 1:
                price, = d6_cursor.fetchone()
    else:
        r = d6_cursor.execute('select value from perla.last_purchase_price where sku = %s;', (item.sku, ))
        if r == 1:
            price, = d6_cursor.fetchone()
    d6_cursor.close()
    d6.close()
    return price
