class Column():
    def __init__(self):
        self.fieldname = None
        self.orientation = Sorter.ASC


class Columns(list):
    def add(self, fieldname, orientation=None):
        if orientation is None:
            orientation = Sorter.ASC
        column = Column()
        column.fieldname = fieldname
        column.orientation = orientation
        self.append(column)
        return column


class Sorter(object):
    ASC = 1
    DESC = -1

    def __init__(self):
        self.columns = Columns()

    def sort(self, list, left=None, right=None):

        if left is None and right is None:
            left = 0
            right = len(list) - 1 if len(list) > 0 else 0

        if left < right:
            point = self.partition(list, left, right)
            from concurrent.futures import ThreadPoolExecutor
            pool = ThreadPoolExecutor(max_workers=100)

            # b = ProcessPoolExecutor()
            a = pool.submit(self.sort, list, left, point - 1)
            b = pool.submit(self.sort, list, point + 1, right)
            # self.sort(list, left, point - 1)
            # self.sort(list, point + 1, right)
            a.result()
            b.result()
            pool.shutdown(wait=True)
            # b.shutdown(wait=True)

    def partition(self, list, left, right) -> int:
        pivot = list[left]
        leftmark = left + 1
        rightmark = right

        while True:
            while leftmark <= rightmark and self.isordered(list[leftmark], pivot):
                leftmark += 1

            while leftmark <= rightmark and self.isordered(pivot, list[rightmark]):
                rightmark -= 1

            if leftmark > rightmark:
                list[left], list[rightmark] = list[rightmark], list[left]
                return rightmark
            else:
                list[leftmark], list[rightmark] = list[rightmark], list[leftmark]

    def isordered(self, left, right):
        for column in self.columns:
            if column.fieldname not in left and column.fieldname in right:
                return True if column.orientation == Sorter.ASC else False
            elif column.fieldname in left and column.fieldname not in right:
                return False if column.orientation == Sorter.ASC else True
            elif column.fieldname in left and column.fieldname in right:
                if not left[column.fieldname] == right[column.fieldname]:
                    if left[column.fieldname] <= right[column.fieldname]:
                        return True if column.orientation == Sorter.ASC else False
                    else:
                        return False if column.orientation == Sorter.ASC else True
        else:
            return True


if __name__ == '__main__':
    # from sarah.acp_bson import Client
    # from pprint import pprint
    #
    # item = {'sku': '1269', 'description': '12 maruchan habanero'}
    #
    # agent_perla = Client('alejandro', 'perla')
    #
    # answer = agent_perla({'type_message': 'find', 'type': 'perla/purchase_price', 'query': {'my_item': item}})
    # prices = answer['result']
    # answer = agent_perla({'type_message': 'find', 'type': 'perla/provider_offer_price', 'query': {'my_item': item}})
    #
    # for price in answer['result']:
    #     prices.append(price)
    #
    # # pprint(prices)
    #
    # sorter = Sorter()
    # sorter.columns.append(Column())
    # sorter.columns[0].fieldname = 'datetime'
    # sorter.columns[0].orientation = Sorter.ASC
    #
    # sorter.sort(prices)
    #
    # pprint(prices)
    from katherine import d6_config, pymysql
    d6 = pymysql.connect(**d6_config)
    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
    print(d6_cursor.execute('select * from valentine.transaction;'))
    txs = d6_cursor.fetchall()
    print(len(txs))
    sorter = Sorter()
    sorter.columns.add('datetime', 1)
    sorter.sort(txs)
    print('ready')
