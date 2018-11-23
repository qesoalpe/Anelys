from isis.main_window import Main_Window
from isis.widget import Widget
from isis.table_view import Table_View
from PySide2.QtWidgets import QSplitter
from isis.h_box_layout import H_Box_Layout
from isis.event import Event
from itzamara import key_to_sort_item
from datetime import datetime
from isodate import datetime_isoformat
from utils import find_one
from isis.data_model.table import Table
from decimal import Decimal as D
from isis.valentine.add_item_quanty import Add_Item_Quanty
from isis.message_box import Message_Box
from dict import Dict as dict, List as list


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.readonly = True


class Count_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('count', D, '#,##0.###')
        self.readonly = True
        self.columns['sku'].getter_data = lambda x: x.item.sku if 'item' in x and 'sku' in x.item else None
        self.columns['description'].getter_data = lambda x: x.item.description if 'item' in x and 'description' in x.item else None


class Entries_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('datetime', str)
        self.columns.add('sku', str)
        self.columns.add('description', str)
        self.columns.add('quanty', D, '#,##0.###')

        self.columns['sku'].getter_data = lambda x: x.item.sku if 'item' in x and 'sku' in x.item else None
        self.columns['description'].getter_data = lambda x: x.item.description if 'item' in x and 'description' in x.item else None

        self.readonly = True


class Create_Physical_Count(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.cwidget = Widget(self)
        self.resize(1400, 700)
        self.setWindowTitle('Crear Conteo Fisico')
        self.tableitems = Table_View(self.cwidget)
        self.tablecount = Table_View(self.cwidget)
        self.tableentries = Table_View(self.cwidget)

        self.itemsmodel = Items_Model()
        self.countmodel = Count_Model()
        self.entriesmodel = Entries_Model()

        self.tableitems.model = self.itemsmodel
        self.tablecount.model = self.countmodel
        self.tableentries.model = self.entriesmodel

        self.splitter = QSplitter(self.cwidget)
        self.splitter.addWidget(self.tableitems)
        self.splitter.addWidget(self.tablecount)
        self.splitter.addWidget(self.tableentries)

        layoutmain = H_Box_Layout(self.cwidget)
        layoutmain.addWidget(self.splitter)
        self.cwidget.layout = layoutmain

        toolbar = self.addToolBar('file')
        action_create = toolbar.addAction('Crear')
        action_open_counter = toolbar.addAction('Abrir Contador')

        action_create.triggered.connect(self.create)
        action_open_counter.triggered.connect(self.open_counter)
        self.physical_count_created = Event()
        self.storage = None
        self.count_global = None

    @property
    def items(self):
        return self.itemsmodel.datasource

    @items.setter
    def items(self, items):
        items.sort(key=key_to_sort_item)
        self.itemsmodel.datasource = items

        count = list()
        def h(item):
            count.append({'item': item, 'count': 0})

        for item in items:
            if 'related' in item:
                for i in item.related['items']:
                    h(i)
            else:
                h(item)
        count.sort(key=key_to_sort_item)

        self.countmodel.datasource = count

        self.entriesmodel.datasource = list()

    def create(self):
        if self.storage is None:
            Message_Box.warning(self, 'Error', 'Debe contener un almacen')
            return

        pc = dict({'datetime': datetime_isoformat(datetime.now())})
        pc.storage = self.storage

        if self.count_global is not None:
            pc.coung_global = {'id': self.count_global.id, 'type': self.count_global.type}

        items = list()
        for item in self.itemsmodel.datasource:
            items.append({'sku': item.sku, 'description': item.description})
        pc['items'] = items
        items.sort(key=key_to_sort_item)

        count = list()
        for item in self.countmodel.datasource:
            count.append({'sku': item.item.sku, 'description': item.item.description, 'count': item.count})
            count.sort(key=key_to_sort_item)
        pc.count = count

        entries = list()
        for entry in self.entriesmodel.datasource:
            entries.append({'sku': entry.item.sku, 'description': entry.item.description,
                            'datetime': entry.datetime, 'quanty': entry.quanty})
        pc.entries = entries
        from sarah.acp_bson import Client
        agent_valentine = Client('', 'valentine')
        answer = agent_valentine({'type_message': 'action', 'action': 'valentine/create_physical_count',
                                  'physical_count': pc})
        if 'error' in answer:
            Message_Box.warning(self, 'Error', 'Ha sucecido un error al crear el conteo fisico')
            return
        else:
            self.physical_count_created(answer.physical_count)
            self.close()

    def open_counter(self):
        d = Add_Item_Quanty(self)
        repo = list([i.item for i in self.countmodel.datasource])
        d.itemsrepository = repo
        d.add_item_quanty.suscribe(self.add_item_quanty)
        d.show()

    def add_item_quanty(self, item, quanty):
        entry = dict({'datetime': datetime_isoformat(datetime.now()), 'item': item, 'quanty': quanty})
        self.entriesmodel.add_row(entry)
        i = find_one(lambda x: x.item.sku == item.sku, self.countmodel.datasource)
        i.count += quanty
        self.countmodel.notify_row_changed(i)
