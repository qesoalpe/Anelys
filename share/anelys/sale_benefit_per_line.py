from katherine import d1
from neo4j.v1 import GraphDatabase, basic_auth
from dict import List
import dictutils
from functools import reduce


d5 = GraphDatabase.driver('bolt://comercialpicazo.com', auth=basic_auth('alejandro', '47exI4'))

lines = List()

sales.s = List([s for s in d1.serena.sale.find({'datetime': re.compile('2017-12.*')}, {'_id': False})])
dictutils.list_float_to_dec(sales.s)
sales.total = round(reduce(lambda x, y: x + y.amount, sales.s, 0), 2)
