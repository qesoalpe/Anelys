import pymysql
import datetime
from datetime import date as date_cls, timedelta
from isodate import parse_date
import re
from decimal import Decimal as D
from dict import Dict
from katherine import d6_config as d8757_6_config, d1 as d8757_1
from isoweek import Week

maria_config = d8757_6_config
maria_conn = pymysql.connect(**maria_config)

maria_cursor = maria_conn.cursor()

coll_sale = d8757_1.serena.sale

default_center = Dict({'id': '42-3', 'type': 'serena/store'})
center_default = default_center


def get_next_month(mm):
    n_month = mm.month
    n_year = mm.year
    if n_month >= 12:
        n_month = 1
        n_year += 1
    else:
        n_month += 1
    return datetime.date(n_year, n_month, 1)


def get_sales_per_date(date=None, center=None):
    if date is None:
        date = date_cls.today()
    elif isinstance(date, str):
        date = parse_date(date)
    if center is None:
        center = default_center
    total_sale = D()
    for sale in coll_sale.find({'datetime': re.compile(date.strftime('%Y-%m-%d') + '.*')},
                               {'amount': True, 'total': True, '_id': False}):
        if 'amount' in sale:
            total_sale += round(D(sale.amount), 2)
        elif 'total' in sale:
            total_sale += round(D(sale.total), 2)
    return total_sale


def sync_sales_per_date(date=None, center=None, cursor=None):
    if center is None:
        center = center_default

    if date is None:
        date = date_cls.today()

    if cursor is None:
        d6 = pymysql.connect(**d8757_6_config)
        cursor = d6.cursor()
    else:
        d6 = None

    total_sale = get_sales_per_date(date, center)

    cursor.execute('insert serena.sales_per_date (date, sales, center_id, center_type) values (%s, %s, %s, %s) '
                   'on duplicate key update sales=values(sales);',
                   (date, total_sale, center.id, center.type))

    if d6 is not None:
        cursor.close()
        d6.close()


def get_sales_per_week(week=None, center=None):
    if week is None:
        week = Week.thisweek()
    elif isinstance(week, str):
        week = Week.fromstring(week)

    if center is None:
        center = default_center

    f = {'datetime': {'$gte': week.monday().strftime('%Y-%m-%d'),
                      '$lt': (week.sunday() + timedelta(days=1)).strftime('%Y-%m-%d')}}

    total_sales = D()
    for s in coll_sale.find(f, {'_id': False, 'amount': True, 'total': True}):
        if 'amount' in s:
            total_sales += round(D(s.amount), 2)
        elif 'total' in s:
            total_sales += round(D(s.amount), 2)
    return total_sales


def sync_sales_per_week(week=None, center=None, cursor=None):
    if center is None:
        center = default_center
    if week is None:
        week = Week.thisweek()
    if cursor is None:
        d6 = pymysql.connect(**d8757_6_config)
        cursor = d6.cursor()
    else:
        d6 = None

    sales = get_sales_per_week(week, center)

    cursor.execute('INSERT serena.sales_per_week (week, center_id, center_type, sales) '
                   'VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE sales = VALUES(sales)',
                   (week.isoformat(), center.id, center.type, sales))

    if d6 is not None:
        cursor.close()
        d6.close()


def get_sales_per_month(month, center):
    f = {'datetime': re.compile(month.strftime('%Y-%m') + '.*')}
    total_sales = D()
    for s in coll_sale.find(f, {'_id': False, 'amount': True, 'total': True}):
        if 'amount' in s:
            total_sales += round(D(s.amount), 2)
        elif 'total' in s:
            total_sales += round(D(s.total), 2)
    return total_sales


def sync_sales_per_month(month=None, center=None, cursor=None):
    if center is None:
        center = default_center
    if month is None:
        month = date_cls.today()
    if cursor is None:
        d6 = pymysql.connect(**d8757_6_config)
        cursor = d6.cursor()
    else:
        d6 = None

    sales = get_sales_per_month(month, center)

    cursor.execute('INSERT serena.sales_per_month (month, center_id, center_type, sales) VALUES (%s, %s, %s, %s) '
                   'ON DUPLICATE KEY UPDATE sales=values(sales);',
                   (month.strftime('%Y-%m'), center.id, center.type, sales))

    if d6 is not None:
        cursor.close()
        d6.close()


def sync_sales_yearly(year, center=None, _d6_cursor=None):
    if center is None:
        center = default_center
    if _d6_cursor is None:
        _d8757_6 = pymysql.connect(**d8757_6_config)
        _d6_cursor = _d8757_6.cursor()
        close_conn = True
    else:
        close_conn = False
        _d8757_6 = None

    _d6_cursor.execute("SELECT SUM(gnucash_sales), SUM(sales) FROM serena.sales_daily "
                       "WHERE center_id = %s and YEAR(DATE) = %s;", (center['id'], year))
    gnucash, serena = _d6_cursor.fetchone()
    _d6_cursor.execute("INSERT serena.sales_per_year(year, center_id, center_type, gnucash_sales, sales) VALUES "
                       "(%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE gnucash_sales=values(gnucash_sales), "
                       "sales=values(sales);",
                       (year, center['id'], center['type'], gnucash, serena))
    if close_conn:
        _d6_cursor.close()
        _d8757_6.close()

