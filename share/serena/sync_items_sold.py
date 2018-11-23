import datetime
import isodate
import re
from sarah.dictutils import float_to_dec
from katherine import d6_config, pymysql, d1 as d8757_1


d8757_6 = pymysql.connect(**d6_config)

store = {'id': '42-3', 'type': 'serena/store'}

def sync_items_sold_by_day(day):
    items_sold = list()
    for sale in d8757_1.serena.sale.find({'datetime': re.compile(isodate.date_isoformat(day) + '.*')}, {'items': True, '_id': False}):
        float_to_dec(sale)
        if 'items' in sale:
            for item in sale['items']:
                for item_sold in items_sold:
                    if item_sold['item']['sku'] == item['sku']:
                        item_sold['quanty'] += item['quanty']
                        break
                else:
                    item_sold = dict()
                    item_sold['item'] = {'sku': item['sku'], 'description': item['description']}
                    if 'type' in item:
                        item_sold['item']['type'] = item['type']
                    item_sold['quanty'] = item['quanty']
                    items_sold.append(item_sold)
    stmt = 'INSERT INTO serena.item_sold_daily (item_sku, item_description, date, quanty, store_id, store_type) ' \
           'VALUES (%(item_sku)s, %(item_description)s, %(date)s, %(quanty)s, %(store_id)s, %(store_type)s) ON ' \
           'DUPLiCATE KEY UPDATE quanty = VALUES(quanty);'
    d6_cursor = d8757_6.cursor()
    for item_sold in items_sold:
        d6_cursor.execute(stmt, {'item_sku': item_sold['item']['sku'],
                                 'item_description': item_sold['item']['description'],
                                 'date': day, 'quanty': item_sold['quanty'], 'store_id': store['id'],
                                 'store_type': store['type']})

if __name__ == '__main__':
    d6_cursor = d8757_6.cursor()
    d6_cursor.execute('select max(date) from serena.item_sold_daily where store_id = %s limit 1;', (store['id'],))
    start, = d6_cursor.fetchone()
    start -= datetime.timedelta(days=1)
    end = datetime.date.today()
    dd = start
    while dd <= end:
        print(isodate.date_isoformat(dd))
        sync_items_sold_by_day(dd)
        dd += datetime.timedelta(days=1)
