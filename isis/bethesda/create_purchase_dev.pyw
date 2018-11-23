from isis.decimal_edit import Decimal_Edit
from isis.label import Label
from decimal import Decimal, Decimal as D
from isodate import datetime_isoformat
from datetime import datetime
from isis.itzamara.search_item import Search_Item
from isis.bethesda.select_document_purchase_without_purchase import Select_Document_Purchase_Without_Purchase
from sarah.acp_bson import Client
from copy import deepcopy
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
from isis.utils import format_currency
from dict import List as list, Dict as dict
from isis.message_box import Message_Box
from isis.main_window import Main_Window
from isis.widget import Widget
from PySide2.QtCore import Qt
from isis.line_edit import Line_Edit
from isis.grid_layout import Grid_Layout
from isis.v_box_layout import V_Box_Layout
from isis.h_box_layout import H_Box_Layout
from isis.push_button import Push_Button
from isis.dialog import Dialog


class Model_Items(Table):
    def __init__(self):
        Table.__init__(self)
        self.provider = None
        self.columns.add('provider_sku', str)
        self.columns.add('provider_description', str)
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', D, 'c')
        self.columns.add('amount', D, 'c')

        def gt_provider_sku(item):
            if 'provider_item' in item and 'sku' in item.provider_item:
                return item.provider_item.sku

        def gt_provider_description(item):
            if 'provider_item' in item and 'description' in item.provider_item:
                return item.provider_item.description

        self.columns['provider_sku'].getter_data = gt_provider_sku
        self.columns['provider_description'].getter_data = gt_provider_description
        self.columns['amount'].getter_data = lambda x: x.quanty * x.price if 'quanty' in x and 'price' in x else None

        self.columns['provider_sku'].changing_value = self.handle_changing_provider_sku
        self.columns['provider_description'].changing_value = self.handle_changing_provider_description
        self.columns['sku'].changing_value = self.handle_changing_sku
        self.columns['description'].changing_value = self.handle_changing_description
        self.columns['price'].changing_value = self.handle_changing_price
        self.columns['amount'].changing_value = self.handle_changing_amount
        self.with_new_empty_row = True
        self.agent_itzamara = Client('', 'itzamara')

    def change_provider(self, provider):
        self.provider = provider

    def flags(self, index):
        if index.column() in [self.columns['provider_sku'].index, self.columns['provider_description'].index]:
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            if self.provider is None:
                flags ^= Qt.ItemIsEditable
            elif not self.is_the_new_empty_row(index.row()):
                item = self.items[index.row()]
                if 'from_document' in item and item.from_document:
                    flags ^= Qt.ItemIsEditable
            return flags
        else:
            return Table.flags(self, index)

    def total_amount(self):
        amount = D()
        for item in self.datasource:
            if 'quanty' in item and 'price' in item:
                amount += item.price * item.quanty
        return amount

    def set_item(self, i, item):
        result = item
        item = self.datasource[i]

        if 'sku' in result:
            item['sku'] = result['sku']
        elif 'sku' in item:
            del item['sku']

        if 'type' in result:
            item['type'] = result['type']
        elif 'type' in item:
            del item['type']

        if 'description' in result:
            item['description'] = result['description']
        elif 'description' in item:
            del item['description']

        if 'price' not in item:
            from perla.prices import get_last_purchase_price
            price = get_last_purchase_price(item)
            if price is not None:
                item.price = price

    def remove_item_data(self, i):
        item = self.datasource[i]
        if 'sku' in item:
            del item['sku']
        if 'type' in item:
            del item['type']
        if 'description' in item:
            del item['description']

    def handle_changing_provider_sku(self, index, value):
        if self.provider is not None and 'id' in self.provider:
            item = self.items[index]
            if value is not None and value:
                if not ('provider_item' in item and 'sku' in item.provider_item and item.provider_item == value):
                    provider = self.provider
                    from katherine import d6_config, pymysql
                    d6 = pymysql.connect(**d6_config)
                    d6_cursor = d6.cursor(pymysql.cursors.DictCursor)
                    r = d6_cursor.execute('select provider_item_description, local_item_sku, local_item_description, '
                                          'price_value from perla.purchase_price '
                                          'where provider_id = %s and provider_item_sku = %s '
                                          'order by datetime desc limit 1;', (provider.id, value))
                    if 'provider_item' not in item:
                        item.provider_item = dict()
                    provider_item = item.provider_item
                    if r == 1:
                        r = dict(d6_cursor.fetchone())

                        provider_item.sku = value
                        provider_item.description = r.provider_item_description
                        if 'sku' not in item:
                            from itzamara.remote import find_one_item
                            itz_item = find_one_item(query={'sku': r.local_item_sku})
                            if itz_item is not None:
                                item.sku = itz_item.sku
                                item.description = itz_item.description

                        if 'price' not in item:
                            item.price = D(r.price_value)
                    else:
                        provider_item.sku = value
                    d6_cursor.close()
                    d6.close()
            elif 'provider_item' in item and 'sku' in item.provider_item:
                del item.provider_item.sku
            else:
                return False
        else:
            return False

    def handle_changing_provider_description(self, index, value):
        item = self.items[index]
        if value is not None and value:
            if 'provider_item' not in item:
                item.provider_item = dict()
            item.provider_item.description = value
        elif 'provider_item' in item and 'description' in item.provider_item:
            provider_item = item.provider_item
            if 'sku' in provider_item:
                del provider_item.description
            else:
                del item.provider_item
        else:
            return False

    def handle_changing_sku(self, index, value):
        item = self.items[index]
        if value is not None and value:
            if 'sku' in item and item['sku'] == value:
                return
            msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': value}}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer['result'] is not None:
                result = answer['result']
                if 'sku' not in item or result.sku != item.sku:
                    self.set_item(index, result)
        elif 'sku' in item:
            self.remove_item_data(index)
        else:
            return False

    def handle_changing_quanty(self, index, value):
        item = self.items[index]
        if value is not None and value > Decimal():
            item.quanty = value
        elif 'quanty' in item:
            del item.quanty
        return False

    def handle_changing_description(self, index, value):
        item = self.items[index]
        if value is not None and value:
            if 'description' in item and item['description'] == value:
                return
            searcher = Search_Item()
            result = searcher.search(value)
            if result is not None:
                self.set_item(index, result)
            else:
                self.remove_item_data(index)
        elif 'description' in item:
            self.remove_item_data(index)
        else:
            return False

    items = Table.datasource

    def handle_changing_price(self, index, value):
        item = self.items[index]
        if value is not None and value > 0:
            item.price = round(value, 2)
        elif 'price' in item:
            del item.price
        else:
            return False

    def handle_changing_amount(self, index, value):
        item = self.items[index]
        if value is not None and value > 0:
            if 'quanty' in item:
                item.price = round(value / item.quanty, 2)
        elif 'price' in item:
            del item.price
        else:
            return False

    def insert_item(self, item):
        self.add_row(item)


class Table_View_Items(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectItems)
        self.enable_delete_row_with_supr = True


class Model_Documents(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('type', str)
        self.columns.add('folio', str)
        self.columns.add('datetime', str)
        self.columns.add('value', D, 'c')

    def total_value(self):
        value = D()
        for doc in self.datasource:
            if 'value' in doc:
                value += doc.value
        return value

    def insert_item(self, item):
        self.add_row(item)


class Table_View_Documents(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)


class Choose_From(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.from_ = None
        btn_select_document_purchase_without_purchase = Push_Button('document_purchase_without_purchase', self)
        layoutmain = V_Box_Layout(self)
        layoutmain.addWidget(btn_select_document_purchase_without_purchase)
        self.setLayout(layoutmain)
        btn_select_document_purchase_without_purchase.clicked.connect(
            self.handle_btn_select_document_purchase_without_purchase_clicked)

    def handle_btn_select_document_purchase_without_purchase_clicked(self):
        self.from_ = 'bethesda/document_purchase_without_purchase'
        self.close()


class Create_Purchase(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Create_Purchase')
        self.resize(1100, 600)
        self.cwidget = Widget(self)
        self.setCentralWidget(self.cwidget)
        cwidget = self.cwidget
        self.widgetprovider = Widget_Viewer_Provider(self.cwidget)
        self.widgetstorage = Widget_Viewer_Storage(self.cwidget)
        self.widgetprovider.with_button_change = True
        self.widgetstorage.with_button_change = True

        lbl_documents_amount = Label('documents amount: ', cwidget)
        lbl_items_amount = Label('items amount: ', cwidget)
        lbl_amount = Label('amount: ', cwidget)
        lbl_datetime = Label('datetime: ', cwidget)
        self.lbl_documents_amount = Label(cwidget)
        self.lbl_items_amount = Label(cwidget)
        self.dec_amount = Decimal_Edit(cwidget)
        self.txt_datetime = Line_Edit(cwidget)

        self.txt_datetime.setFixedWidth(100 + 50)
        self.dec_amount.setMaximum(1000000)
        self.dec_amount.setMinimum(0)

        lbl_documents_amount.fix_size_based_on_font()
        lbl_items_amount.fix_size_based_on_font()
        lbl_amount.fix_size_based_on_font()
        lbl_datetime.fix_size_based_on_font()

        self.tableviewitems = Table_View_Items(cwidget)
        self.tableviewdocuments = Table_View_Documents(cwidget)

        headerlayout = Grid_Layout()
        headerlayout.addWidget(lbl_documents_amount, 0, 0)
        headerlayout.addWidget(self.lbl_documents_amount, 0, 1)
        headerlayout.addWidget(lbl_items_amount, 1, 0)
        headerlayout.addWidget(self.lbl_items_amount, 1, 1)
        headerlayout.addWidget(lbl_amount, 0, 2)
        headerlayout.addWidget(self.dec_amount, 0, 3)
        headerlayout.addWidget(lbl_datetime, 1, 2)
        headerlayout.addWidget(self.txt_datetime, 1, 3)

        toplayout = H_Box_Layout()
        toplayout.addWidget(self.widgetprovider)
        toplayout.addItem(headerlayout)

        tableslayout = H_Box_Layout()
        tableslayout.addWidget(self.tableviewitems)
        tableslayout.addWidget(self.tableviewdocuments)
        self.tableviewdocuments.setFixedWidth(450)

        layoutmain = V_Box_Layout(cwidget)
        layoutmain.addItem(toplayout)
        layoutmain.addItem(tableslayout)
        layoutmain.addWidget(self.widgetstorage)
        cwidget.setLayout(layoutmain)

        self.modelitems = Model_Items()
        self.tableviewitems.model = self.modelitems

        self.modeldocuments = Model_Documents()
        self.tableviewdocuments.model = self.modeldocuments

        self.create_menus()

        def handle_changes_in_modelitems(*args):
            self.lbl_items_amount.text = format_currency(self.modelitems.total_amount())

        def handle_changes_in_modeldocuments(*args):
            self.lbl_documents_amount.text = format_currency(self.modeldocuments.total_value())

        self.widgetprovider.provider_changed.suscribe(self.modelitems.change_provider)
        self.modelitems.any_change_in_datasource.suscribe(handle_changes_in_modelitems)
        self.modeldocuments.any_change_in_datasource.suscribe(handle_changes_in_modeldocuments)

        self.agent_itzamara = Client('create_purchase', 'itzamara')
        self.agent_bethesda = Client('create_purchase', 'bethesda')

    def create_menus(self):
        doc_toolbar = self.addToolBar('document')
        action_create = doc_toolbar.addAction('create')
        action_load_document = doc_toolbar.addAction('load_document')

        action_create.triggered.connect(self.create)
        action_load_document.triggered.connect(self.load_document)

    @property
    def provider(self):
        return self.widgetprovider.provider

    @provider.setter
    def provider(self, x):
        self.widgetprovider.provider = x

    @property
    def storage(self):
        return self.widgetstorage.storage

    @storage.setter
    def storage(self, x):
        self.widgetstorage.storage = x

    @property
    def items(self):
        return self.modelitems.datasource

    @property
    def documents(self):
        return self.modeldocuments.datasource

    def create(self):
        items = deepcopy(self.items)

        for item in items[:]:
            if 'description' not in item or not item['description']:
                Message_Box.warning(self, 'error', 'todos los articulos deben contener descripcion')
                return
            if 'from_document' in item:
                del item.from_document

        provider = self.provider

        if provider is None:
            Message_Box.warning(self, 'invalid', 'purchase should has a provider valid')
            return

        storage = self.storage

        if storage is None:
            Message_Box.warning(self, 'invalid', 'purchase require a storage')
            return

        purchase = dict({'items': items, 'storage': storage, 'provider': provider})
        if self.txt_datetime.text:
            purchase.datetime = self.txt_datetime.text
        else:
            purchase.datetime = datetime_isoformat(datetime.now())

        documents = self.documents
        if len(documents) == 1:
            purchase.document = documents[0]
        elif len(documents) > 1:
            purchase.documents = documents

        if self.modeldocuments.total_value() != 0:
            purchase.amount = self.modeldocuments.total_value()
        elif self.dec_amount.value != 0:
            purchase.amount = self.dec_amount.value
        elif self.modelitems.total_amount() != 0:
            purchase.amount = self.modelitems.total_amount()
        else:
            Message_Box.warning(self, 'error', 'amount should be given of any of the three ways')
            return

        tolerancy_rate = D('0.005')
        if abs(purchase.amount - self.modelitems.total_amount()) > purchase.amount * tolerancy_rate:
            Message_Box.warning(self, 'invalid', 'amounts pass the tolerancy')
            return

        msg = {'type_message': 'action', 'action': 'bethesda/create_purchase', 'purchase': purchase}
        answer = self.agent_bethesda(msg)

        if 'error' in answer:
            Message_Box.warning(self, 'error', 'an error has happened')
            return
        else:
            Message_Box.information(self, 'success', 'purchase created successfully')
            self.close()

    def load_document(self):
        choosing = Choose_From(self)
        choosing.exec_()
        if choosing.from_ is not None:
            doc = None
            if choosing.from_ == 'bethesda/document_purchase_without_purchase':
                selecter = Select_Document_Purchase_Without_Purchase(self, provider=self.provider)
                selecter.exec_()

                if selecter.selected is not None:
                    doc = selecter.selected
            if doc is not None:
                if 'id' in doc:
                    for doc_in in self.documents:
                        if 'id' in doc_in and doc['id'] == doc_in['id']:
                            Message_Box.information(self, 'already exists', 'document already exists in purchase')
                            return
                if self.provider is None and 'provider' in doc:
                    self.provider = deepcopy(doc['provider'])

                if doc['type'] in ['bethesda/invoice', 'bethesda/note_credit', 'bethesda/ticket', 'bethesda/remission',
                                   'bethesda/sale_note', 'bethesda/return_note', 'bethesda/charge_note']:
                    rr = Message_Box.question(self, 'document value', 'document is of value?',
                                              Message_Box.Yes | Message_Box.No)
                    if rr == Message_Box.Yes:
                        if 'value' not in doc:
                            if 'balance' in doc:
                                doc['value'] = doc['balance']
                            elif 'amount' in doc:
                                doc['value'] = doc['amount']
                            elif 'total' in doc:
                                doc['value'] = doc['total']
                            if doc['type'] not in ['bethesda/invoice', 'bethesda/remission', 'bethesda/sale_note',
                                                   'bethesda/ticket', 'bethesda/note_charge'] and 'value' in doc:
                                doc['value'] = -doc['value']

                if doc['type'] in ['bethesda/invoice', 'bethesda/sale_note', 'bethesda/ticket', 'bethesda/remission'] and 'items' in doc:
                    rr = Message_Box.question(self, 'pass items', 'pass document\'s items at purchase\'s items',
                                              Message_Box.Yes | Message_Box.No)
                    if rr == Message_Box.Yes:
                        try:
                            from katherine import d6_config, pymysql
                            d6 = pymysql.connect(**d6_config)
                            d6_cursor = d6.cursor()
                        except:
                            d6 = None
                            d6_cursor = None
                        for doc_item in doc['items']:
                            item = dict()
                            provider_item = dict()
                            if 'sku' in doc_item and self.provider is not None and 'id' in self.provider:
                                provider_item['sku'] = doc_item['sku']
                                if d6_cursor is not None:
                                    r = d6_cursor.execute('select distinct local_item_sku from perla.purchase_price '
                                                          'where provider_id = %s and provider_item_sku = %s;',
                                                          (self.provider['id'], provider_item['sku']))
                                    if r == 1:
                                        sku, = d6_cursor.fetchone()
                                        answer = self.agent_itzamara({'type_message': 'find_one', 'query': {'sku': sku},
                                                                      'type': 'itzamara/item'})
                                        if 'result' in answer and answer['result'] is not None:
                                            result = answer['result']
                                            if 'sku' in result:
                                                item['sku'] = result['sku']
                                            if 'description' in result:
                                                item['description'] = result['description']
                            if 'description' in doc_item:
                                provider_item['description'] = doc_item['description']
                            item['provider_item'] = provider_item
                            if 'quanty' in doc_item:
                                item['quanty'] = doc_item['quanty']
                            if 'price' in doc_item:
                                item['price'] = doc_item['price']
                            item.from_document = True
                            self.modelitems.add_row(item)
                        if d6_cursor is not None:
                            d6_cursor.close()
                        if d6 is not None:
                            d6.close()
                for k in list(doc.keys()):
                    if k not in ['id', 'type', 'document_type', 'value', 'folio', 'datetime']:
                        del doc[k]

                self.modeldocuments.add_row(doc)


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Create_Purchase()
    vv.show()
    sys.exit(app.exec_())
