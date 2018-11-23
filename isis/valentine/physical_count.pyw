from isis.event import Event
from PySide.QtGui import *
from PySide.QtCore import *
from isis.table_view import Table_View
from isis.data_model.table import Table
from decimal import Decimal
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
from isis.itzamara.search_item import Search_Item
from isis.itzamara.search_item_list import Search_Item_List
from isis.dialog import Dialog
from isis.decimal_edit import Decimal_Edit
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.dialog_search_text import Dialog_Search_Text


class MainWindow(QMainWindow):
    pass


class Select_Counting(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Select_Counting')
        self.resize(700, 450)
        lbl_search = Label('search: ', self)
        lbl_counting = Label('counting', self)
        lbl_counting_related = Label('counting_related', self)

        self.txt_search = Line_Edit(self)

        self.viewcounting = Table_View(self)
        self.viewcounting_related = Table_View(self)

        layoutmain = QGridLayout(self)
        layoutsearch = QHBoxLayout()
        layoutsearch.addWidget(lbl_search)
        layoutsearch.addWidget(self.txt_search)

        layoutmain.addLayout(layoutsearch, 0, 0, 1, -1)
        layoutmain.addWidget(lbl_counting, 1, 0)
        layoutmain.addWidget(self.viewcounting, 2, 0)
        layoutmain.addWidget(lbl_counting_related, 1, 1)
        layoutmain.addWidget(self.viewcounting_related, 2, 1)

        self.counting = Table()
        self.counting.columns.add('sku', str)
        self.counting.columns.add('description', str)
        self.counting.readonly = True

        self.counting_related = Table()
        self.counting_related.columns.add('sku', str)
        self.counting_related.columns.add('description', str)
        self.counting_related.readonly = True

        self.viewcounting.model = self.counting
        self.viewcounting_related.model = self.counting_related

        self.txt_search.key_down.suscribe(self.handle_txt_search_key_down)

    def handle_txt_search_key_down(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            searcher = Dialog_Search_Text(self)
            from copy import deepcopy
            from pprint import pprint
            from sorter import Sorter

            def _help(m):
                result = list()
                e = deepcopy(m)
                searcher = Search_Item()
                searcher.searching(e)
                if 'selected' in e:
                    result.append(e['selected'])
                if 'list' in e:
                    result.extend(e['list'])
                searcher = Search_Item_List()
                e = deepcopy(m)
                searcher.searching(e)
                if 'selected' in e:
                    result.append(e['selected'])
                if 'list' in e:
                    result.extend(e['list'])
                sorter = Sorter()
                sorter.columns.add('name')
                sorter.columns.add('description')
                sorter.sort(result)
                table = Table()
                table.columns.add('type', str)
                table.columns.add('id | sku', str)
                table.columns[1].getter_data = lambda x: x['id'] if 'id' in x else x['sku'] if 'sku' in x else None
                table.columns.add('name | description', str)
                table.columns[2].getter_data = lambda x: x['name'] if 'name' in x else x['description'] if 'description' in x else None
                table.datasource = result
                table.readonly = True
                m['table'] = table
                m['list'] = result
            searcher.searching = _help
            result = searcher.search(self.txt_search.text)
            self.txt_search.text = None
            if result is not None:
                def _item_in_counting(item):
                    try:
                        if item['sku'] in [item['sku'] for item in self.counting_related.datasource]:
                            return True
                        else:
                            return False
                    except:
                        pprint(item)

                if isinstance(result, dict):
                    if 'type' not in result or result['type'] == 'itzamara/item':
                        if _item_in_counting(result):
                            QMessageBox.warning(self, 'error', '%s: %s already in counting' % (result['sku'], result['description']))
                            return
                    elif result['type'] == 'itzamara/item_list':
                        for item in result['items'][:]:
                            if _item_in_counting(item):
                                result['items'].remove(item)

                from itzamara.rpc import get_items_factor_related
                result = get_items_factor_related(result)
                if isinstance(result, dict) and ('type' not in result or result['type'] == 'itzamara/item'):
                    for itemrelated in result['items_related']:
                        if _item_in_counting(itemrelated):
                            QMessageBox.warning(self, 'error',
                                                '%s: %s already in counting' % (result['sku'], result['description']))
                            return
                    item = result
                    self.counting.datasource.append(item)
                    from copy import deepcopy
                    countingrelated = deepcopy(item)
                    for k in list(countingrelated.keys()):
                        if k not in ['sku', 'type', 'description']:
                            del countingrelated[k]
                    self.counting_related.datasource.append(countingrelated)
                    for itemrelated in item['items_related']:
                        countingrelated = deepcopy(itemrelated)
                        for k in list(countingrelated.keys()):
                            if k not in ['sku', 'type', 'description']:
                                del countingrelated[k]
                        self.counting_related.datasource.append(countingrelated)

                elif isinstance(result, dict) and result['type'] == 'itzamara/item_list' and 'items' in result:
                    for item in result['items'][:]:
                        for itemrelated in item['items_related']:
                            if _item_in_counting(itemrelated):
                                result['items'].remove(item)
                                break
                    for item in result['items']:
                        self.counting.datasource.append(item)
                        from copy import deepcopy
                        countingrelated = deepcopy(item)
                        for k in list(countingrelated.keys()):
                            if k not in ['sku', 'type', 'description']:
                                del countingrelated[k]
                        self.counting_related.datasource.append(countingrelated)
                        for itemrelated in item['items_related']:
                            countingrelated = deepcopy(itemrelated)
                            for k in list(countingrelated.keys()):
                                if k not in ['sku', 'type', 'description']:
                                    del countingrelated[k]
                            self.counting_related.datasource.append(countingrelated)

                elif isinstance(result, list):
                    for item in result:
                        for itemrelated in item['items_related']:
                            if _item_in_counting(itemrelated):
                                result.remove(item)
                                break
                    for item in result:
                        self.counting.datasource.append(item)
                        from copy import deepcopy
                        countingrelated = deepcopy(item)
                        for k in list(countingrelated.keys()):
                            if k not in ['sku', 'type', 'description']:
                                del countingrelated[k]
                        self.counting_related.datasource.append(countingrelated)
                        if 'items_related' in item:
                             for itemrelated in item['items_related']:
                                countingrelated = deepcopy(itemrelated)
                                for k in list(countingrelated.keys()):
                                    if k not in ['sku', 'type', 'description']:
                                        del countingrelated[k]
                                self.counting_related.datasource.append(countingrelated)
                self.counting_related.update_all()
                self.counting.update_all()


class Counter(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.setWindowTitle('Counter')
        self.resize(500, 100)
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        lbl_quanty = Label('quanty: ', self)

        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()

        self.lbl_sku = Label(self)
        self.txt_description = Line_Edit(self)
        self.dec_quanty = Decimal_Edit(self)
        self.dec_quanty.minimum = -1000
        self.dec_quanty.maximum = 1000

        btn_register = QPushButton('register', self)

        mainlayout = QVBoxLayout(self)
        layoutitem = QGridLayout()
        layoutitem.addWidget(lbl_sku, 0, 0)
        layoutitem.addWidget(self.lbl_sku, 0, 1)
        layoutitem.addWidget(lbl_description, 1, 0)
        layoutitem.addWidget(self.txt_description, 1, 1)
        layoutitem.addWidget(lbl_quanty, 2, 0)
        layoutitem.addWidget(self.dec_quanty)
        mainlayout.addLayout(layoutitem)
        mainlayout.addWidget(btn_register)
        mainlayout.addStretch(1)

        self.txt_description.key_down.suscribe(self.handle_txt_description_key_down)
        self.txt_description.text_edited.suscribe(self.handle_txt_description_text_edited)
        self.setLayout(mainlayout)

        self.counting = list()
        self._item = None
        self.register = lambda x, y: print('happened', x)

        def gg(event):
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.pre_register()

        # self.key_down.suscribe(gg)
        self.dec_quanty.key_down.suscribe(gg)

    def pre_register(self):
        if self.item is not None and self.dec_quanty.value is not None:
            self.register(self.item, self.dec_quanty.value)
            self.item = None
            self.dec_quanty.value = None
            self.txt_description.focus()

    def handle_txt_description_key_down(self, event):
        if isinstance(event, QEvent):
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                searcher = Search_Item(self)
                result = searcher.search(self.txt_description.text)
                if result is not None:
                    self.item = result
                else:
                    self.item = None
                event.accept()

    def handle_txt_description_text_edited(self, text):
        self.lbl_sku.text = None
        self._item = None

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item
        if item is not None:
            if item['sku'] not in [item['sku'] for item in self.counting]:
                QMessageBox.warning(self, 'error', '%s: %s not in counting' % (item['sku'], item['description']))
                self.lbl_sku.text = None
                self.txt_description.text = None
                return
            self.lbl_sku.text = item['sku']
            self.txt_description.text = item['description']
            self.dec_quanty.focus()
        else:
            self.lbl_sku.text = None
            self.txt_description.text = None


class Count_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('count', Decimal) # '#,##0.###')
        self.readonly = True


class Count_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)


class Entry_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('datetime', str)
        self.columns.add('sku', str)
        self.columns['sku'].getter_data = lambda x: x['item']['sku'] if 'item' in x and 'sku' in x['item'] else None
        self.columns.add('description', str)
        self.columns['description'].getter_data = lambda x: x['item']['description'] if 'item' in x and 'description' in x['item'] else None
        self.columns.add('quanty', Decimal)
        self.readonly = True


class Physical_Count(MainWindow):
    def __init__(self):
        MainWindow.__init__(self)
        self.setWindowTitle('Physical_Count')
        self.resize(800, 600)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        the_tabs = QTabWidget(self.cwidget)
        self.count_table = Count_Table_View(the_tabs)
        self.entries_table = Table_View(the_tabs)

        the_tabs.addTab(self.count_table, 'count')
        the_tabs.addTab(self.entries_table, 'entries')

        self.count_model = Count_Model()
        self.entries_model = Entry_Model()

        self.count_table.model = self.count_model
        self.entries_table.model = self.entries_model
        self.viewer_storage = Widget_Viewer_Storage(self.cwidget)

        btn_open_counter = QPushButton('open counter', self.cwidget)
        btn_open_counter.setMinimumWidth(100)
        btn_cancel_count = QPushButton('cancel counter', self.cwidget)
        btn_cancel_count.setMinimumWidth(100)
        btn_print_count = QPushButton('print count', self.cwidget)
        btn_new_count = QPushButton('new count', self.cwidget)
        btn_finish_count = QPushButton('finish count', self.cwidget)

        layoutmain = QHBoxLayout(self.cwidget)
        layoutmain.addWidget(the_tabs)
        rightlayout  = QVBoxLayout()
        # layoutbuttons.addStretch(50)
        rightlayout.addWidget(self.viewer_storage)
        layoutbuttons = QGridLayout()
        layoutbuttons.addWidget(btn_open_counter, 0, 0)
        layoutbuttons.addWidget(btn_cancel_count, 0, 1)
        layoutbuttons.addWidget(btn_print_count, 1, 0)
        layoutbuttons.addWidget(btn_new_count, 1, 1)
        layoutbuttons.addWidget(btn_finish_count, 2, 0, 1, -1)
        # layoutbuttons.addStretch(1)
        rightlayout.addLayout(layoutbuttons)
        rightlayout.addStretch(1)
        layoutmain.addLayout(rightlayout)
        self.cwidget.setLayout(layoutmain)

        self._storage = None

        self.count_model.datasource = list()
        self.entries_model.datasource = list()
        self.counting = list()

        self.storage_changed = Event()
        self.viewer_storage.with_button_change = True

        self.storage = {'address': 'Ignacio Manuel Altamirano #17, col. Jose Lopez Portillo, Villa Juarez, Navolato, '
                                   'Sinaloa, 80378', 'id': '42-3',
                        'name': 'Tienda Altamirano', 'storage_type': 'serena/store', 'type': 'valentine/storage'}
        self.counting = list()

        def handle():
            counter = Counter(self)
            counter.counting = self.count
            counter.show()
            counter.register = self.register_entries

        btn_open_counter.clicked.connect(handle)
        btn_cancel_count.clicked.connect(lambda: self.cancel_count(True))
        btn_new_count.clicked.connect(self.new_count)

    @property
    def storage(self):
        return self.viewer_storage.storage

    @storage.setter
    def storage(self, storage):
        self.viewer_storage.storage = storage
        self.storage_changed(storage)

    @property
    def count(self):
        return self.count_model.datasource

    @count.setter
    def count(self, counting):
        self.count_model.datasource = counting

    @property
    def entries(self):
        return self.entries_model.datasource

    @entries.setter
    def entries(self, entries):
        self.entries_model.datasource = entries

    def new_count(self):
        cc = Select_Counting(self)
        cc.exec_()
        self.count = cc.counting_related.datasource
        self.counting = cc.counting.datasource

    def cancel_count(self, request=False):
        if request:
            r = QMessageBox.question(self, 'sure', 'seguro de cancelar? no se recuperaran los datos',
                                     QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.No:
                return
        self.counting = list()
        self.entries = list()

    def register_entries(self, item, quanty):
        from copy import deepcopy
        from datetime import datetime
        from isodate import datetime_isoformat
        entry = {'item': deepcopy(item), 'datetime': datetime_isoformat(datetime.now()), 'quanty': quanty}
        self.entries_model.add_row(entry)
        for itemcounting in self.count:
            if itemcounting['sku'] == item['sku']:
                break
        else:
            itemcounting = None

        if itemcounting is not None:
            itemcounting['count'] = itemcounting['count'] + quanty if 'count' in itemcounting else quanty
            self.count_model.notify_row_changed(itemcounting)


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Physical_Count()
    vv.show()
    sys.exit(app.exec_())
