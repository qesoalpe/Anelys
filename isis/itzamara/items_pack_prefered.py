from isis.main_window import Main_Window
from isis.widget import Widget
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.h_box_layout import H_Box_Layout
from katherine import d6_config, pymysql
from dict import List as list
from itzamara import key_to_sort_item
from utils import find_one
from PySide2.QtCore import Qt
from isis.menu import Menu
from isis.event import Event


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.readonly = True


class TV_Items_Prefered(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.unprefered = Event()

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.unprefered(index.row())
        Table_View.mouseDoubleClickEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = Menu(self)
                menu.addAction('unset prefered')

                menu.triggered.connect(lambda: self.unprefered(index.row()))
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class TV_Items_With_No_Prefered(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.set_prefered = Event()

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.set_prefered(index.row())
        Table_View.mouseDoubleClickEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = Menu(self)
                menu.addAction('set prefered')

                menu.triggered.connect(lambda: self.set_prefered(index.row()))
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class Items_Pack_Prefered(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(1200, 800)
        self.setWindowTitle('Items Pack Prefered')
        self.cwidget = Widget(self)

        self.tvitemsprefered = TV_Items_Prefered(self.cwidget)
        self.tvitemswithnoprefered = TV_Items_With_No_Prefered(self.cwidget)

        self.itemsprefered = Items_Model()
        self.itemswithnoprefered = Items_Model()

        main_layout = H_Box_Layout()
        main_layout.addWidget(self.tvitemsprefered)
        main_layout.addWidget(self.tvitemswithnoprefered)
        self.cwidget.layout = main_layout

        self.tvitemsprefered.model = self.itemsprefered
        self.tvitemswithnoprefered.model = self.itemswithnoprefered

        d6 = pymysql.connect(**d6_config)
        d6_cursor = d6.cursor(pymysql.cursors.SSDictCursor)
        d6_cursor.execute('select sku, description from itzamara.item '
                          'where sku in (select item_pack_id from itzamara.item_pack) '
                          'or sku in (select item_factor_id from itzamara.item_pack)')
        self.items = list([item for item in d6_cursor])
        self.items.sort(key=key_to_sort_item)
        d6_cursor.close()
        d6_cursor = d6.cursor(pymysql.cursors.SSCursor)
        d6_cursor.execute('select item_pack_id, item_factor_id from itzamara.item_pack;')
        self.relateds = list()
        for pack_sku, item_sku in d6_cursor:
            pack = find_one(lambda x: x.sku == pack_sku, self.items)
            item = find_one(lambda x: x.sku == item_sku, self.items)

            if 'related' in pack and 'related' not in item:
                pack.related.append(item)
                item.related = pack.related
            elif 'related' in item and 'related' not in pack:
                item.related.append(pack)
                pack.related = item.related
            elif 'related' in pack and 'related' in item:
                related = pack.related
                for r in item.related:
                    if r.sku not in [i.sku for i in related]:
                        related.append(r)
                        r.related = related
            else:
                related = list([pack, item])
                pack.related = related
                item.related = related
                self.relateds.append(related)

        d6_cursor.execute('select sku from itzamara.item_prefered;')
        prefered = list([sku for sku, in d6_cursor])
        itemsprefered = list()
        for p in prefered:
            i = find_one(lambda x: x.sku == p, self.items)
            itemsprefered.append(i)
        itemsprefered.sort(key=key_to_sort_item)
        self.itemsprefered.datasource = itemsprefered
        itemswithnoprefered = list()
        for item in self.items:
            if item.sku not in prefered:
                if 'related' in item:
                    for sku in [i.sku for i in item.related]:
                        if sku in prefered:
                            break
                    else:
                        itemswithnoprefered.append(item)
                else:
                    itemswithnoprefered.append(item)
        itemswithnoprefered.sort(key=key_to_sort_item)
        self.itemswithnoprefered.datasource = itemswithnoprefered
        d6_cursor.close()
        d6.close()

        self.tvitemsprefered.unprefered.suscribe(self.handle_tv_prefered_unset_prefered)
        self.tvitemswithnoprefered.set_prefered.suscribe(self.handle_tv_no_prefered_set_prefered)
        # pprint(find_one(lambda x: x.sku == '4345', self.items).related)

    def handle_tv_prefered_unset_prefered(self, index):
        item = self.itemsprefered.datasource[index]
        self.itemsprefered.remove_row(item)
        if 'related' in item:
            for r in item.related:
                self.itemswithnoprefered.add_row(r)
        d6 = pymysql.connect(**d6_config)
        cursor = d6.cursor()
        r = cursor.execute('delete from itzamara.item_prefered where sku = %s;', (item.sku, ))
        cursor.close()
        d6.close()

    def handle_tv_no_prefered_set_prefered(self, index):
        item = self.itemswithnoprefered.datasource[index]
        if item not in self.itemsprefered.datasource:
            self.itemsprefered.add_row(item)

        if 'related' in item:
            for r in item.related:
                if r in self.itemswithnoprefered.datasource:
                    self.itemswithnoprefered.remove_row(r)
        else:
            if item in self.itemswithnoprefered.datasource:
                self.itemswithnoprefered.remove_data(item)
        d6 = pymysql.connect(**d6_config)
        cursor = d6.cursor()
        r = cursor.execute('insert ignore itzamara.item_prefered values (%s, %s);', (item.sku, item.description))
        cursor.close()
        d6.close()


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Items_Pack_Prefered()
    mw.show()
    sys.exit(app.exec_())
