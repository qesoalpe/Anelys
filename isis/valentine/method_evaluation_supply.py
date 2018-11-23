from isis.main_window import Main_Window
from isis.data_model.table import Table
from decimal import Decimal as D
from isis.widget import Widget
from isis.table_view import Table_View
from isis.h_box_layout import H_Box_Layout
from dict import Dict as dict, List as list
from itzamara import key_to_sort_item
from utils import find_one
from katherine import d6_config, pymysql, d1
from pprint import pprint
from isis.combo_box import Combo_Box
from PySide2.QtWidgets import QStyledItemDelegate
from isis.menu import Menu
from isis.event import Event
from PySide2.QtCore import Qt


repo_storage = list([s for s in d1.valentine.storage.find()])
repo_supplier = list([s for s in d1.valentine.supplier.find()])

d6 = pymysql.connect(**d6_config)


class Method_Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 2:
            editor = Combo_Box(parent)
            editor.addItems(['itemdemand', 'maximum'])
            return editor


d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
r = d6_cursor.execute('select * from itzamara.item_prefered where sku not in (select sku from itzamara.item);')

if r > 0:
    print('precaucion existen item_prefered que no estan en itzamara.item')
    print('los articulos son los siguientes')
    print(d6_cursor.fetchall())
    print('se eliminaran los item_prefered que no aparecen en itzamara.item')
    d6_cursor.execute('delete from itzamara.item_prefered where sku not in (select sku from itzamara.item);')
    print('hecho')
d6_cursor.close()


class Items_Method_Evaluation_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('method', str)
        self.columns.add('inventory', D, '#,##0.###')
        self.columns.add('demand', str)
        self.columns.add('maximum', D, '#,##0.###')
        self.columns.add('reorder_point', D, '#,##0.###')
        self.columns.add('demand_maximum', str)
        self.columns.add('demand_reorder_point', str)

        self.datasource = list()

        self.columns['method'].changing_item_value = self.changing_item_value_method
        self.columns['maximum'].changing_item_value = self.changing_item_value_maximum
        self.columns['reorder_point'].changing_item_value = self.changing_item_value_reorder_point
        self.columns['demand_maximum'].changing_item_value = self.changing_item_value_demand_maximum
        self.columns['demand_reorder_point'].changing_item_value = self.changing_item_value_demand_reorder_point

        self.columns['sku'].getter_data = self.getter_data_sku
        self.columns['description'].getter_data = self.getter_data_description
        self.readonly = False
        self.columns['sku'].readonly = True
        self.columns['description'].readonly = True
        self.columns['inventory'].readonly = True
        self.columns['demand'].readonly = True

        self.storage = None

    @staticmethod
    def getter_data_sku(row):
        if 'item' in row and 'sku' in row.item:
            return row.item.sku
        elif 'item_sku' in row:
            return row.item_sku
        elif 'sku' in row:
            return row.sku

    @staticmethod
    def getter_data_description(row):
        if 'item' in row and 'description' in row.item:
            return row.item.description
        elif 'item_description' in row:
            return row.item_description
        elif 'description' in row:
            return row.description

    def changing_item_value_method(self, item, value):
        d6.ping()
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('update valentine.method_evaluation_supply set method = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s;',
                              (value, item.item.sku, self.storage.id, item.supplier.id))
        else:
            d6_cursor.execute('update valentine.method_evaluation_supply set method = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id is NULL;',
                              (value, item.item.sku, self.storage.id))
        d6_cursor.close()
        if value is not None:
            item.method = value
        elif 'method' in item:
            del item.method

    def changing_item_value_maximum(self, item, value):
        d6.ping(True)
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('update valentine.method_evaluation_supply set maximum = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s;',
                              (value, item.item.sku, self.storage.id, item.supplier.id))
        else:
            d6_cursor.execute('update valentine.method_evaluation_supply set maximum = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id IS NULL;',
                              (value, item.item.sku, self.storage.id))
        d6_cursor.close()
        if value is not None:
            item.maximum = value
        elif 'maximum' in item:
            del item.maximum

    def changing_item_value_reorder_point(self, item, value):
        d6.ping(True)
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('update valentine.method_evaluation_supply set reorder_point = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s limit 1;',
                              (value, item.item.sku, self.storage.id, item.supplier.id))
        else:
            d6_cursor.execute('update valentine.method_evaluation_supply set reorder_point = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id IS NULL limit 1;',
                              (value, item.item.sku, self.storage.id))
        d6.close()
        if value is not None:
            item.reorder_point = value
        elif 'reorder_point' in item:
            del item.reorder_point

    def changing_item_value_demand_maximum(self, item, value):
        d6.ping(True)
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('update valentine.method_evaluation_supply set demand_maximum = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s limit 1;',
                              (value, item.item.sku, self.storage.id, self.supplier.id))
        else:
            d6_cursor.execute('update valentine.method_evaluation_supply set demand_maximum = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id IS NULL limit 1;',
                              (value, item.item.sku, self.storage.id))
        d6_cursor.close()

        if value is not None:
            item.demand_maximum = value
        elif 'demand_maximum' in item:
            del item.demand_maximum

    def changing_item_value_demand_reorder_point(self, item, value):
        d6.ping(True)
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('update valentine.method_evaluation_supply set demand_reorder_point = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s limit 1;',
                              (value, item.item.sku, self.storage.id, self.supplier.id))
        else:
            d6_cursor.execute('update valentine.method_evaluation_supply set demand_reorder_point = %s '
                              'where item_sku = %s and storage_id = %s and supplier_id IS NULL limit 1;',
                              (value, item.item.sku, self.storage.id))
        d6_cursor.close()

        if value is not None:
            item.demand_reorder_point = value
        elif 'demand_reorder_point' in item:
            del item.demand_reorder_point


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.readonly = True
        self.datasource = list()


class TV_Items_Method(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setItemDelegateForColumn(2, Method_Delegate())
        self.remove_from_method = Event()
        self.set_item_not_supplied = Event()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = Menu(self)
                action = menu.addAction('Remove from method')
                action.triggered.connect(lambda: self.remove_from_method(index.row()))
                action = menu.addAction('set item not supplied')
                action.triggered.connect(lambda: self.set_item_not_supplied(index.row()))
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class TV_Items(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.set_item_not_supplied = Event()
        self.add_item_to_method = Event()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = Menu(self)
                action = menu.addAction('Set not item supplied')
                action.triggered.connect(lambda: self.set_item_not_supplied(index.row()))
                action = menu.addAction('Add item to method')
                action.triggered.connect(lambda: self.add_item_to_method(index.row()))
                menu.popup(event.globalPos())

        Table_View.mousePressEvent(self, event)


class TV_Items_Not_Supplied(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.remove_item_not_supplied = Event()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = Menu(self)
                action = menu.addAction('Remove item not supplied')
                action.triggered.connect(lambda: self.remove_item_not_supplied(index.row()))
                menu.popup(event.globalPos())

        Table_View.mousePressEvent(self, event)


class Method_Evaluation_Supply(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        from PySide2.QtWidgets import QSplitter
        self.resize(1500, 800)
        self.setWindowTitle('Method Evaluation Supply')
        self.cwidget = Widget()
        self.tvitemsmethod = TV_Items_Method(self.cwidget)
        self.tvitems = TV_Items(self.cwidget)
        self.tvitemsnotsupplied = TV_Items_Not_Supplied(self.cwidget)
        splitter = QSplitter(self.cwidget)
        splitter.addWidget(self.tvitemsmethod)
        splitter.addWidget(self.tvitems)
        splitter.addWidget(self.tvitemsnotsupplied)

        layout_main = H_Box_Layout(self.cwidget)
        layout_main.addWidget(splitter)
        self.cwidget.layout = layout_main

        self.modelitemsmethod = Items_Method_Evaluation_Model()
        self.modelitems = Items_Model()
        self.modelitemsnotsupplied = Items_Model()

        self.tvitemsmethod.model = self.modelitemsmethod
        self.tvitems.model = self.modelitems
        self.tvitemsnotsupplied.model = self.modelitemsnotsupplied
        # toolbar = self.addToolBar('File')

        self.storage = d1.valentine.storage.find_one({'id': '42-3'}, {'_id': False})
        self.modelitemsmethod.storage = self.storage

        d6.ping(True)
        d6_cursor = d6.cursor(pymysql.cursors.SSDictCursor)
        d6_cursor.execute('select sku, description from itzamara.item;')

        self.items = list(d6_cursor.fetchall())
        self.items.sort(key=key_to_sort_item)
        d6_cursor.close()

        d6_cursor = d6.cursor(pymysql.cursors.SSCursor)
        d6_cursor.execute('select pack_sku, item_sku from itzamara.pack;')
        self.relateds = list()
        for pack_sku, item_sku in d6_cursor:
            pack = find_one(lambda x: x.sku == pack_sku, self.items)
            item = find_one(lambda x: x.sku == item_sku, self.items)

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
                self.relateds.append(related)

        d6_cursor.execute('select sku from itzamara.item_prefered;')

        itemsprefered = list()
        for sku, in d6_cursor:
            i = find_one(lambda x: x.sku == sku, self.items)
            if 'related' in i:
                if 'prefered' in i.related:
                    print('the next related has more of one prefered')
                    pprint(i.related)
                i.related.prefered = i
            itemsprefered.append(i)
        self.itemsprefered = itemsprefered

        d6_cursor.execute('select sku from valentine.item_not_supplied where storage_id = %s;', (self.storage.id, ))
        items_not_supplied = list()
        for sku, in d6_cursor:
            i = find_one(lambda x: x.sku == sku, self.items)
            if i is not None:
                if 'related' in i and 'prefered' in i.related:
                    items_not_supplied.append(i.related.prefered)
                else:
                    items_not_supplied.append(i)
        d6_cursor.close()

        items_not_supplied_sku = [item.sku for item in items_not_supplied]

        for relateds_not_supplied in [item.related for item in items_not_supplied if 'related' in item]:
            for item in relateds_not_supplied['items']:
                if item.sku not in items_not_supplied_sku:
                    items_not_supplied_sku.append(item.sku)

        d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
        d6_cursor.execute('select * from valentine.method_evaluation_supply where storage_id = %s;', (self.storage.id, ))

        self.itemsmethod = list(d6_cursor.fetchall())
        d6_cursor.close()

        for item in self.itemsmethod:
            i = find_one(lambda x: x.sku == item.item_sku, self.items)
            if i is not None:
                item.item = i
                del item.item_sku
                del item.item_description
            if 'supplier_id' in item:
                if item.supplier_id is not None:
                    s = find_one(lambda x: x.id == item.supplier_id, repo_supplier)
                    if s is not None:
                        item.supplier = s
                    else:
                        item.supplier = {'id': item.supplier_id}
                del item.supplier_id

        items_method_sku = list()
        for item in self.itemsmethod:
            if 'related' in item.item:
                for ir in item.item.related['items']:
                    if ir.sku not in items_method_sku:
                        items_method_sku.append(ir.sku)
            elif item.item.sku not in items_method_sku:
                items_method_sku.append(item.item.sku)

        items = list([item for item in self.items if 'related' not in item or 'prefered' not in item.related])
        prefereds = [item.related.prefered for item in self.items if 'related' in item and 'prefered' in item.related]
        for item in prefereds:
            if item not in items:
                items.append(item)
        not_items_sku = items_not_supplied_sku + items_method_sku
        items = list([item for item in items if item.sku not in not_items_sku])

        items.sort(key=key_to_sort_item)
        items_not_supplied.sort(key=key_to_sort_item)
        self.itemsmethod.sort(key=lambda x: key_to_sort_item(x.item))
        self.modelitemsmethod.datasource = self.itemsmethod
        self.modelitems.datasource = items
        self.modelitemsnotsupplied.datasource = items_not_supplied

        self.tvitems.add_item_to_method.suscribe(self.handle_tv_items_add_item_to_method)
        self.tvitems.set_item_not_supplied.suscribe(self.handle_tv_items_set_item_not_supplied)
        self.tvitemsnotsupplied.remove_item_not_supplied.suscribe(self.handle_tv_items_not_supplied_remove_items_not_supplied)
        self.tvitemsmethod.remove_from_method.suscribe(self.handle_tv_items_method_remove_from_method)
        # pprint(find_one(lambda x: x.sku == '4551', self.items).related['items'])

        toolbar = self.addToolBar('file')
        action_update_inventory = toolbar.addAction('Actualizar Inventario')
        action_update_demand = toolbar.addAction('Actualizar Demanda')
        action_update_inventory.triggered.connect(self.update_inventory)
        action_update_demand.triggered.connect(self.update_demand)

    def update_inventory(self):
        from valentine.remote import get_inventory_absolut

        items = [{'sku': item.item.sku, 'description': item.item.description} for item in self.modelitemsmethod.datasource if 'item' in item and 'sku' in item.item]
        inventory = get_inventory_absolut(items, self.storage)
        items = [item for item in self.modelitemsmethod.datasource if 'sku' in item.item]
        for item, inventory in zip(items, inventory):
            item.inventory = inventory.inventory_absolut
        self.modelitemsmethod.modelReset.emit()

    def update_demand(self):
        from isis.utils import format_number
        d6.ping()
        d6_cursor = d6.cursor()
        storage_id = self.storage.id
        for item in self.modelitemsmethod.datasource:
            r = d6_cursor.execute('select period, demand from valentine.item_demand '
                                  'where storage_id = %s and item_sku = %s limit 1;',
                                  (storage_id, item.item.sku))
            if r == 1:
                period, demand = d6_cursor.fetchone()
                item.demand = format_number(demand) + '/' + period

        d6_cursor.close()
        self.modelitemsmethod.modelReset.emit()

    def handle_tv_items_method_remove_from_method(self, i):
        item = self.modelitemsmethod.datasource[i]
        d6.ping(True)
        d6_cursor = d6.cursor()
        if 'supplier' in item:
            d6_cursor.execute('delete from valentine.method_evaluation_supply '
                              'where item_sku = %s and storage_id = %s and supplier_id = %s;',
                              (item.item.sku, self.storage.id, item.supplier.id))
        else:
            d6_cursor.execute('delete from valentine.method_evaluation_supply '
                              'where item_sku = %s and storage_id = %s and supplier_id IS NULL;',
                              (item.item.sku, self.storage.id))
        d6_cursor.close()
        self.modelitemsmethod.remove_row(i)
        item = item.item

        if 'related' in item and 'prefered' in item.related:
            self.modelitems.add_row(item.related.prefered)
        elif 'related' in item and 'prefered' not in item.related:
            for ir in item.prefered['items']:
                self.modelitems.add_row(ir)
        else:
            self.modelitems.add_row(item)

    def handle_tv_items_add_item_to_method(self, i):
        item = self.modelitems.datasource[i]
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('insert valentine.method_evaluation_supply '
                          '(storage_id, storage_type, item_sku, item_description, method) '
                          'values (%s, %s, %s, %s, %s);',
                          (self.storage.id, self.storage.type, item.sku, item.description, 'itemdemand'))
        itemmethod = dict({'item': item, 'method': 'itemdemand'})
        self.modelitemsmethod.add_row(itemmethod)
        if 'related' in item and 'prefered' not in item.related:
            for ir in item.related['items']:
                if ir in self.modelitems.datasource:
                    self.modelitems.remove_row(ir)
        else:
            self.modelitems.remove_row(i)

    def handle_tv_items_set_item_not_supplied(self, i):
        item = self.modelitems.datasource[i]
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('insert ignore valentine.item_not_supplied (storage_id, sku) values (%s, %s);',
                          (self.storage.id, item.sku))
        d6_cursor.close()
        if ('related' in item and 'prefered' in item.related) or ('related' not in item):
            self.modelitems.remove_row(i)
        else:
            for related in item.related['items']:
                if related in self.modelitems.datasource:
                    self.modelitems.remove_row(related)

        self.modelitemsnotsupplied.add_row(item)

    def handle_tv_items_not_supplied_remove_items_not_supplied(self, i):
        item = self.modelitemsnotsupplied.datasource[i]
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('delete from valentine.item_not_supplied where storage_id = %s and sku = %s;',
                          (self.storage.id, item.sku))
        d6_cursor.close()

        self.modelitemsnotsupplied.remove_row(i)

        if 'related' in item and 'prefered' in item.related:
            self.modelitems.add_row(item.related.prefered)
        elif 'related' in item and 'prefered' not in item.related:
            for ir in item.prefered['items']:
                self.modelitems.add_row(ir)
        else:
            self.modelitems.add_row(item)


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    mw = Method_Evaluation_Supply()
    mw.show()
    sys.exit(app.exec_())
