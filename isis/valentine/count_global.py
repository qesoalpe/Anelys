from katherine import d1, d6_config, pymysql
from dict import Dict as dict, List as list
from utils import find_one
from isis.main_window import Main_Window
from isis.dialog import Dialog
from isis.widget import Widget
from isis.data_model.table import Table
from isis.table_view import Table_View
from itzamara import key_to_sort_item
from isis.v_box_layout import V_Box_Layout
from isis.valentine.create_physical_count import Create_Physical_Count
from PySide2.QtWidgets import QSplitter
import dictutils


d6 = pymysql.connect(**d6_config)

d6_cursor = d6.cursor(pymysql.cursors.SSDictCursor)

d6_cursor.execute('select sku, description from itzamara.item;')

itzamara = dict()
itzamara['items'] = list(d6_cursor.fetchall())

d6_cursor.close()

d6_cursor = d6.cursor(pymysql.cursors.SSCursor)
d6_cursor.execute('select item_pack_id, item_factor_id from itzamara.item_pack;')
itzamara.relateds = list()

for pack_sku, item_sku in d6_cursor:
    pack = find_one(lambda x: x.sku == pack_sku, itzamara['items'])
    item = find_one(lambda x: x.sku == item_sku, itzamara['items'])

    if 'related' in pack and 'related' not in item:
        pack.related['items'].append(item)
        item.related = pack.related
    elif 'related' in item and 'related' not in pack:
        item.related['items'].append(pack)
        pack.related = item.related
    elif 'related' in pack and 'related' in item:
        related = pack.related
        for r in item.related['items']:
            if r.sku not in [i.sku for i in related['items']]:
                related['items'].append(r)
                r.related = related
    else:
        related = dict({'items': [pack, item]})
        pack.related = related
        item.related = related
        itzamara.relateds.append(related)


cg = d1.valentine.count_global.find_one({'id': '215-2'}, {'_id': False})
l = list()
lr = list()

for count in cg.counts:
    items = list()
    for item in count['items']:
        i = find_one(lambda x: x.sku == item.sku, itzamara['items'])
        items.append(i)
    count['items'] = items

for item in cg['items']:
    i = find_one(lambda x: x.sku == item.sku, itzamara['items'])
    if i is not None:
        l.append(i)
        if 'related' in i:
            lr.extend(i.related['items'])
        else:
            lr.append(i)

cg['items'] = l
cg.items_related = lr


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.readonly = True


class Counts_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('datetime', str)
        self.columns.add('items', int)
        self.readonly = True

        self.columns['items'].getter_data = lambda x: len(x['items'])


class Count_Global(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(900, 800)
        self.setWindowTitle('Conteo Global')
        self.cwidget = Widget(self)

        self.tableitemspending = Table_View(self.cwidget)
        self.tablecounts = Table_View(self.cwidget)

        self.itemspendingmodel = Items_Model()
        self.countsmodel = Counts_Model()

        self.tableitemspending.model = self.itemspendingmodel
        self.tablecounts.model = self.countsmodel
        splitter = QSplitter(self.cwidget)
        splitter.addWidget(self.tableitemspending)
        splitter.addWidget(self.tablecounts)

        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addWidget(splitter)
        self.cwidget.layout = layoutmain

        itemscounted = list()
        for count in cg.counts:
            itemscounted.extend(count['items'])

        itemspending = list([item for item in cg['items'] if item not in itemscounted])
        itemspending.sort(key=key_to_sort_item)

        self.itemspendingmodel.datasource = itemspending
        self.countsmodel.datasource = cg.counts

        toolbar = self.addToolBar('File')
        action_create_count = toolbar.addAction('Crear Conteo')
        action_create_count.triggered.connect(self.create_count)

    def create_count(self):
        from isis.valentine.select_items import Select_Items
        si = Select_Items(self)
        si.itemsrepository = self.itemspendingmodel.datasource
        r = si.exec_()
        if r == Dialog.Accepted:
            cc = Create_Physical_Count()
            cc.count_global = cg
            cc.storage = cg.storage
            cc.items = si.items
            cc.physical_count_created.suscribe(self.handle_count_created)
            cc.show()

    def handle_count_created(self, pc):
        for k in list(pc.keys()):
            if k not in ['id', 'type', 'datetime', 'items']:
                del pc[k]
        dictutils.dec_to_float(pc)
        d1.valentine.count_global.update({'id': cg.id}, {'$push': {'counts': pc}})
        dictutils.float_to_dec(pc)
        items = list()
        for i in pc['items']:
            items.append(find_one(lambda x: x.sku == i.sku, itzamara['items']))
        pc['items'] = items
        self.countsmodel.add_row(pc)
        itemscounted = list()
        for count in cg.counts:
            itemscounted.extend(count['items'])

        itemspending = list([item for item in cg['items'] if item not in itemscounted])
        itemspending.sort(key=key_to_sort_item)
        self.itemspendingmodel.datasource = itemspending


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    mw = Count_Global()
    mw.show()
    sys.exit(app.exec_())
