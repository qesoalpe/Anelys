import pymysql
from isoweek import Week
from datetime import timedelta
from dict import Dict
from katherine import d6_config as d6_connection_config, d1, d6_config
import re
from functools import reduce
from decimal import Decimal as D
from isodate import date_isoformat

center_default = Dict({'id': '42-3'})

from valentine import sales_cost as sales_cost_mod

print('starting to update sales_costs')
sales_cost_mod.update_sales_cost()
print('ending at update sales_costs')


def get_costs_per_date(date, center=None):
    sales_cost = d1.valentine.sale_cost.find({'datetime': re.compile(date.strftime('%Y-%m-%d') + '.*')},
                                             {'_id': False, 'cost': True})

    return reduce(lambda x, y: x + round(D(y.cost), 2), [sc for sc in sales_cost], 0)


def sync_costs_per_date(date, center=None, cursor=None):
    if center is None:
        center = center_default

    if date > date.today():
        raise Exception('date should not be out of time')
    if cursor is None:
        d6 = pymysql.connect(**d6_connection_config)
        cursor = d6.cursor()
    else:
        d6 = None

    t = get_costs_per_date(date, center)
    cursor.execute('insert valentine.costs_per_date(center_id, date, costs) values (%s, %s, %s) on duplicate key '
                   'update  costs = values(costs);', (center.id, date, t))
    if d6 is not None:
        cursor.close()
        d6.close()


def get_costs_per_week(week):
    if isinstance(week, str):
        week = Week.fromstring(week)
    elif not isinstance(week, Week):
        raise TypeError(week)
    sales_cost = d1.valentine.sale_cost.find({'datetime': {'$gte': date_isoformat(week.monday()),
                                                           '$lt': date_isoformat(week.sunday() + timedelta(days=1))}},
                                             {'_id': False, 'cost': True})
    sales_cost = [sc for sc in sales_cost]
    return reduce(lambda x, y: x + round(D(y.cost), 2), sales_cost, 0)


def sync_costs_per_week(week=None, center=None):
    if week is None:
        week = Week.thisweek()
    elif isinstance(week, str):
        week = Week.fromstring(week)

    if center is None:
        center = center_default

    costs = get_costs_per_week(week)
    d6 = pymysql.connect(**d6_config)
    cursor = d6.cursor()
    cursor.execute('insert valentine.costs_per_week(center_id, week, costs) values (%s, %s, %s) '
                   'on duplicate key update costs = values(costs);',
                   (center.id, week.isoformat(), costs))
    cursor.close()
    d6.close()


def get_costs_per_month(month):
    sales_cost = d1.valentine.sale_cost.find({'datetime': re.compile(month.strftime('%Y-%m') + '.*')},
                                             {'_id': False, 'cost': True})
    sales_cost = [sc for sc in sales_cost]
    return reduce(lambda x, y: x + round(D(y.cost), 2), sales_cost, 0)


def sync_costs_per_month(month):
    sales_cost = get_costs_per_month(month)
    d6 = pymysql.connect(**d6_config)
    cursor = d6.cursor()
    cursor.execute('INSERT valentine.costs_per_month (center_id, month, costs) values ("42-3", %s, %s) '
                   'ON DUPLICATE KEY UPDATE costs = VALUES(costs);', (month.strftime('%Y-%m'), sales_cost))
    cursor.close()
    d6.close()
