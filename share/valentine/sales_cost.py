from katherine import d1
from katherine import d6_config
import pymysql
from dict import Dict
from decimal import Decimal
from perla.prices import get_last_purchase_price
from datetime import date as date_cls
import dictutils

d6 = pymysql.connect(**d6_config)
d6_cursor = d6.cursor()


def persist_sale_cost_in_d6(sale_cost):
    import dictutils
    dictutils.float_to_dec(sale_cost)
    params = {'id': sale_cost.id, 'amount': round(sale_cost.amount, 2),
              'cost': round(sale_cost.cost, 2),
              'datetime': sale_cost.datetime, 'benefit': round(sale_cost.amount - sale_cost.cost, 2)}

    if 'benefit' in params and params['benefit'] != 0 and 'amount' in sale_cost and sale_cost.amount != 0:
        params['rate'] = round(params['benefit'] / sale_cost.amount * 100, 2)
    else:
        params['rate'] = None

    d6_cursor.execute('insert valentine.sale_cost (id, amount, datetime, cost, benefit, rate) values '
                      '(%(id)s, %(amount)s, %(datetime)s, %(cost)s, %(benefit)s, %(rate)s) on duplicate key '
                      'update amount = values(amount), cost = values(cost), benefit=values(benefit), '
                      'rate = values(rate);', params)


def persist(sale_cost):
    dictutils.dec_to_float(sale_cost)
    d1.valentine.sale_cost.replace_one({'id': sale_cost.id}, sale_cost, upsert=True)
    dictutils.float_to_dec(sale_cost)

    persist_sale_cost_in_d6(sale_cost)


def process_items(items, datetime):

    from perla.prices import get_last_purchase_price

    for item in items:
        price = get_last_purchase_price(item, datetime=datetime)
        if price is not None:
            item.cost = price
        if 'price' in item and isinstance(item.price, Dict) and 'value' in item.price:
            item.price = item.price.value
        elif 'price' in item and isinstance(item.price, (Decimal, int)):
            pass
        elif 'price' in item:
            del item.price

        for k in list(item.keys()):
            if k not in ['sku', 'description', 'price', 'cost', 'quanty']:
                del item[k]


def process_sale(sale):
    items = sale['items']
    process_items(items, sale.datetime)

    from functools import reduce
    try:
        sale.cost = round(reduce(lambda x, y: x + y.quanty * y.cost, list(filter(lambda x: 'cost' in x, items)), 0), 2)
        if 'total' in sale:
            sale.amount = sale.total
            del sale.total
        sale.amount = round(sale.amount, 2)
    except:
        from pprint import pprint
        pprint(sale)
    for k in list(sale.keys()):
        if k not in ['id', 'datetime', 'amount', 'cost', 'type', 'items']:
            del sale[k]


def get_sale_cost(sale=None, sales=None):
    from copy import deepcopy
    import dictutils
    if sale is not None:
        sale = deepcopy(sale)
        dictutils.float_to_dec(sale)
        process_sale(sale)
        return sale
    elif sales is not None:
        sales = deepcopy(sales)
        dictutils.list_float_to_dec(sales)
        for sale in sales:
            process_sale(sale)
        return sales


def get_sales_cost_per_date(date):
    import re
    if isinstance(date, date_cls):
        re_date = re.compile(date.strftime('%Y-%m-%d') + '.*')
    elif isinstance(date, str):
        re_date = re.compile(date + '.*')
    else:
        raise Exception('date arg should be a datetime.date or str {isoformat}')

    sales = [sale for sale in d1.serena.sale.find({'datetime': re_date}, {'_id': False})]
    import dictutils
    dictutils.list_float_to_dec(sales)
    for sale in sales:
        process_sale(sale)
    return sales


def sync_sales_cost_per_date(date):
    import re
    if isinstance(date, date_cls):
        re_date = re.compile(date.strftime('%Y-%m-%d') + '.*')
    elif isinstance(date, str):
        re_date = re.compile(date + '.*')
    else:
        raise Exception('date arg should be a datetime.date or str {isoformat}')

    d6_cursor.execute('delete from valentine.sale_cost where date(datetime) = %s;', (date, ))
    d1.valentine.sale_cost.remove({'datetime': re_date})

    sales_cost = get_sales_cost_per_date(date)
    for sc in sales_cost:
        persist(sc)


def sync_document_sale_and_cost(date):
    db = d1.serena
    colls_document_sale = [db.ticket, db.remission, db.sale_note, db.invoice]

    import re
    from datetime import date as date_cls
    rdate = re.compile(date.strftime('%Y-%m-%d.*')) if isinstance(date, date_cls) else re.compile(date + '.*') \
        if isinstance(date, str) else date

    d6_cursor.execute('delete from serena.document_sale_and_cost where datetime like %s;',
                      (date.strftime('%Y-%m-%d%%') if isinstance(date, date_cls) else date,))

    for coll in colls_document_sale:
        docs = [doc for doc in coll.find({'datetime': rdate}, {'_id': False})]
        ids = [doc.id for doc in docs]
        d1.serena.document_sale_and_cost.remove({'id': {'$in': ids}})


        import dictutils
        dictutils.list_float_to_dec(docs)

        for doc in docs:
            for item in doc['items']:
                price = get_last_purchase_price(item)
                if price is not None:
                    item.cost = price
                if 'price' in item and isinstance(item.price, Dict) and 'value' in item.price:
                    item.price = item.price.value
                elif 'price' in item and isinstance(item.price, (Decimal, int)):
                    pass
                elif 'price' in item:
                    del item.price
                for k in list(item.keys()):
                    if k not in ['sku', 'description', 'price', 'cost', 'quanty']:
                        del item[k]

            from functools import reduce
            try:
                ll = list(filter(lambda x: 'cost' in x, doc['items']))
                doc.cost = round(reduce(lambda x, y: x + y.quanty * y.cost, ll, 0), 2)

                if 'total' in doc:
                    doc.amount = round(doc.total, 2)
                else:
                    doc.amount = round(doc.amount, 2)
            except:
                from pprint import pprint
                pprint(doc)

            for k in list(doc.keys()):
                if k not in ['id', 'datetime', 'total', 'cost', 'type', 'items', 'products', 'amount']:
                    del doc[k]
            try:
                d6_cursor.execute('insert ignore serena.document_sale_and_cost (doc_id, doc_type, amount, datetime, '
                                  'cost, benefit, rate) values (%s, %s, %s, %s, %s, %s, %s);',
                                  (doc.id, doc.type if 'type' in doc else None, doc.amount, doc.datetime, doc.cost,
                                   doc.amount - doc.cost,
                                   round((doc.amount - doc.cost) / doc.amount * 100, 2) if doc.amount != 0 and doc.cost != 0 else None))
            except Exception as e:
                from pprint import pprint
                pprint(doc)
                raise e

            dictutils.dec_to_float(doc)
            r = d1.serena.document_sale_and_cost.insert_one(doc)
            if '_id' in doc: del doc._id;


def sync(date):
    # sync_sale_and_cost(date)
    sync_document_sale_and_cost(date)


def update_sales_cost():
    cursor = d6_cursor
    r = cursor.execute('select max(datetime) from valentine.sale_cost;')
    if r == 1:
        from isodate import datetime_isoformat
        d, = cursor.fetchone()
        f = {'datetime': {'$gte': datetime_isoformat(d)}}
        sales = [s for s in d1.serena.sale.find(f, {'_id': False}, sort=[('datetime', 1)])]
    else:
        sales = [s for s in d1.serena.sale.find({}, {'_id': False}, sort=[('datetime', 1)])]

    length = len(sales)
    chunk_size = 512
    p = 0
    while p < length:
        sales_cost = get_sale_cost(sales=sales[p: p + chunk_size if p + chunk_size < length else length])
        p += chunk_size
        for sale_cost in sales_cost:
            persist(sale_cost)


if __name__ == '__main__':
    update_sales_cost()
