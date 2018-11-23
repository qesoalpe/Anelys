from isis.piper.search_provider import Search_Provider
from sarah.acp_bson import Client
from decimal import Decimal as D
from copy import deepcopy
from isis.haley.select_cfdi_no_attached import Select_Cfdi_No_Attached
from isis.utils import format_currency, parse_number
from dict import Dict
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.main_window import Main_Window
from isis.widget import Widget
from isis.group_box import Group_Box
from isis.push_button import Push_Button
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.grid_layout import Grid_Layout
from isis.h_box_layout import H_Box_Layout
from isis.v_box_layout import V_Box_Layout
from isis.combo_box import Combo_Box
from isis.dialog import Dialog
from isis.main_window import Main_Window
from isis.file_dialog import File_Dialog
from isis.message_box import Message_Box
from dict import Dict as dict, List as list
from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
from isis.text_edit import Text_Edit
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QSpacerItem, QSizePolicy
from isis.haley.loader_cfdi import Loader_Cfdi

ALL_DOCUMENT_TYPE = ['bethesda/invoice', 'bethesda/ticket', 'bethesda/remission', 'bethesda/sale_note',
                     'bethesda/note_credit', 'bethesda/return_note', 'bethesda/charge_note']


class Model_Items(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', D, 'c')
        self.columns.add('amount', D, 'c')

        self.columns['amount'].getter_data = lambda x: x.quanty * x.price if 'quanty' in x and 'price' in x else None

        self.columns['sku'].changing_value = self.changing_value_sku
        self.columns['amount'].changing_value = self.changing_value_amount
        self.datasource = list()
        self.with_new_empty_row = True
        self.provider = None
        self.document_type = None
        self.agent_piper = Client('', 'piper')

    def change_provider(self, provider):
        self.provider = provider

    def change_document_type(self, value):
        self.document_type = value

    def totalamount(self):
        amount = D()
        for data in self.datasource:
            if 'quanty' in data and 'price' in data:
                amount += round(data.quanty * data.price, 2)
        return amount

    def changing_value_sku(self, index, value):
        item = self.datasource[index]
        if value is not None and value:
            if 'sku' in item and item['sku'] == value:
                return
            if self.provider is not None:
                msg = {'type_message': 'find_one', 'type': 'piper/item_document',
                       'document_type': self.document_type, 'query': {'sku': value, 'provider': self.provider}}
                answer = self.agent_piper(msg)
                if 'result' in answer and answer['result'] is not None:
                    result = answer['result']
                    if 'sku' in result:
                        item['sku'] = result['sku']
                    elif 'sku' in item:
                        del item['sku']
                    if 'type' in result:
                        item['type'] = result['type']
                    elif 'type' in item:
                        del item['type']
                    if 'description' in result and 'description' not in item:
                            item['description'] = result['description']
                    if 'price' not in item and 'price' in result and result['price'] is not None:
                        item['price'] = result['price']
                else:
                    item['sku'] = value
            else:
                item['sku'] = value
        elif 'sku' in item:
            del item.sku
        else:
            return False

    def changing_value_amount(self, index, value):
        item = self.datasource[index]
        if value is not None and value > D():
            if 'quanty' in item:
                item['price'] = round(value / item['quanty'], 2)
        elif 'price' in item:
                del item['price']
        else:
            return False


class Table_View_Items(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectItems)
        self.enable_delete_row_with_supr = True


class Create_Document(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Create_Document')
        self.resize(800, 600)
        self.cwidget = Widget(self)
        self.central_widget = self.cwidget
        lbl_type = Label('type: ', self.cwidget)
        lbl_datetime = Label('datetime: ', self.cwidget)
        lbl_folio = Label('folio: ', self.cwidget)

        self.widget_provider = Widget_Viewer_Provider(self.cwidget)
        self.widget_provider.with_button_change = True

        self.cmb_type = Combo_Box(self.cwidget)
        self.txt_datetime = Line_Edit(self.cwidget)
        self.txt_folio = Line_Edit(self.cwidget)

        lbl_cfdi = Label('cfdi', self.cwidget)
        btn_load_cfdi = Push_Button('load_cfdi', self.cwidget)
        lbl_cfdi_uuid = Label('uuid: ', self.cwidget)
        lbl_cfdi_total = Label('total: ', self.cwidget)
        lbl_cfdi_voucher_effect = Label('effect: ', self.cwidget)
        self.lbl_cfdi_uuid = Label(self.cwidget)
        self.lbl_cfdi_total = Label(self.cwidget)
        self.lbl_cfdi_voucher_effect = Label(self.cwidget)
        lbl_amount_items = Label('amount_items: ', self.cwidget)
        lbl_discount = Label('discount: ', self.cwidget)
        lbl_amount = Label('amount: ', self.cwidget)
        lbl_balance = Label('balance: ', self.cwidget)
        lbl_comments = Label('comments', self.cwidget)
        self.lbl_amount_items = Label(self.cwidget)
        self.txt_discount = Line_Edit(self.cwidget)
        self.txt_amount = Line_Edit(self.cwidget)
        self.txt_balance = Line_Edit(self.cwidget)
        self.txt_comments = Text_Edit(self.cwidget)

        self.tableviewitems = Table_View_Items(self.cwidget)

        doclayout = Grid_Layout()
        doclayout.addWidget(lbl_type, 0, 0)
        doclayout.addWidget(self.cmb_type, 0, 1)
        doclayout.addWidget(lbl_datetime, 1, 0)
        doclayout.addWidget(self.txt_datetime, 1, 1)
        doclayout.addWidget(lbl_folio, 2, 0)
        doclayout.addWidget(self.txt_folio)
        cfdilayout = Grid_Layout()
        cfdilayout.addWidget(lbl_cfdi, 0, 0)
        cfdilayout.addWidget(btn_load_cfdi, 0, 1, Qt.AlignRight)
        cfdilayout.addWidget(lbl_cfdi_uuid, 1, 0)
        cfdilayout.addWidget(self.lbl_cfdi_uuid, 1, 1)
        cfdilayout.addWidget(lbl_cfdi_total, 2, 0)
        cfdilayout.addWidget(self.lbl_cfdi_total, 2, 1)
        cfdilayout.addWidget(lbl_cfdi_voucher_effect, 3, 0)
        cfdilayout.addWidget(self.lbl_cfdi_voucher_effect, 3, 1)
        toplayout = H_Box_Layout()
        toplayout.addItem(doclayout)
        toplayout.addWidget(self.widget_provider)
        toplayout.addItem(cfdilayout)
        toplayout.setStretchFactor(doclayout, 20)
        toplayout.setStretchFactor(self.widget_provider, 33)
        toplayout.setStretchFactor(cfdilayout, 33)

        rightlayout = Grid_Layout()
        rightlayout.addWidget(lbl_amount_items, 0, 0)
        rightlayout.addWidget(self.lbl_amount_items, 0, 1)
        rightlayout.addWidget(lbl_discount, 1, 0)
        rightlayout.addWidget(self.txt_discount, 1, 1)
        rightlayout.addWidget(lbl_amount, 2, 0)
        rightlayout.addWidget(self.txt_amount, 2, 1)
        rightlayout.addWidget(lbl_balance, 3, 0)
        rightlayout.addWidget(self.txt_balance, 3, 1)
        rightlayout.addWidget(lbl_comments, 4, 0, 1, -1)
        rightlayout.addWidget(self.txt_comments, 5, 0, 1, -1)
        rightlayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        secondlayout = H_Box_Layout()
        secondlayout.addWidget(self.tableviewitems)
        secondlayout.addItem(rightlayout)
        secondlayout.setStretch(0, 100)

        mainlayout = V_Box_Layout(self.cwidget)
        mainlayout.addItem(toplayout)
        mainlayout.addItem(secondlayout)
        self.cwidget.setLayout(mainlayout)

        main_toolbar = self.addToolBar('main')
        actioncreate = main_toolbar.addAction('create')
        actioncreate.triggered.connect(self.create)

        self.modelitems = Model_Items()
        self.tableviewitems.model = self.modelitems
        self.cmb_type.addItems(ALL_DOCUMENT_TYPE)
        self.modelitems.any_change_in_datasource.suscribe(self.update_amount)
        self.widget_provider.provider_changed.suscribe(self.modelitems.change_provider)
        btn_load_cfdi.clicked.connect(self.handle_btn_load_cfdi)
        self.cmb_type.currentTextChanged.connect(self.modelitems.change_document_type)
        self.modelitems.document_type = self.cmb_type.currentText()
        self._cfdi = None
        self.agent_piper = Client('isis.bethesda.create_document', 'piper')
        self.agent_bethesda = Client('isis.bethesda.create_document', 'bethesda')

    def create(self):
        document = dict()
        document['type'] = self.cmb_type.currentText()
        if not self.txt_datetime.text:
            Message_Box.warning(self, 'invalid', 'es necesario un datetime')
            return
        document['datetime'] = self.txt_datetime.text
        if self.txt_folio.text:
            document['folio'] = self.txt_folio.text

        amount = parse_number(self.txt_amount.text)
        if amount is None:
            Message_Box.warning(self, 'error', 'document should contains amount')
            return
        document['amount'] = amount

        discount = parse_number(self.txt_discount.text)
        if discount is not None:
            document['discount'] = discount
        else:
            discount = D()
        if self.cfdi is not None:
            document['cfdi'] = self.cfdi
        items_amount = self.modelitems.totalamount() - discount
        amount_net = amount

        tolerance_percent = D('0.003')
        tolerance_amount = items_amount * tolerance_percent

        if amount_net < items_amount - tolerance_amount or amount_net > items_amount + tolerance_amount:
            Message_Box.warning(self, 'invalid', 'importe de documento y de articulos esta por fuera de la '
                                                 'tolerancia permitida')
            return

        if self.txt_balance.text:
            document['balance'] = parse_number(self.txt_balance.text)

        items = deepcopy(self.items)
        for item in items[:]:
            if 'description' not in item or 'quanty' not in item or 'price' not in item:
                items.remove(item)
        document['items'] = items
        if self.widget_provider.provider is not None:
            document['provider'] = self.widget_provider.provider
        else:
            Message_Box.warning(self, 'invalid', 'document should contains provider')
            return
        if self.txt_comments.toPlainText():
            document['comments'] = self.txt_comments.toPlainText()

        msg = {'type_message': 'action'}

        if document['type'] == 'bethesda/invoice':
            msg['action'] = 'bethesda/create_invoice'
            msg['invoice'] = document
        elif document['type'] == 'bethesda/note_charge':
            msg['action'] = 'bethesda/create_note_charge'
            msg['note_charge'] = document
        elif document['type'] == 'bethesda/note_credit':
            msg['action'] = 'bethesda/create_note_credit'
            msg['note_credit'] = document
        elif document['type'] == 'bethesda/remission':
            msg['action'] = 'bethesda/create_remission'
            msg['remission'] = document
        elif document['type'] == 'bethesda/return_note':
            msg['action'] = 'bethesda/create_return_note'
            msg['return_note'] = document
        elif document['type'] == 'bethesda/sale_note':
            msg['action'] = 'bethesda/create_sale_note'
            msg['sale_note'] = document
        elif document['type'] == 'bethesda/ticket':
            msg['action'] = 'bethesda/create_ticket'
            msg['ticket'] = document
        answer = self.agent_bethesda(msg)
        if 'error' in answer and answer['error']:
            Message_Box.warning(self, 'error', 'an error has happened')
        else:
            Message_Box.information(self, 'success', 'document was sent successfully')
            self.close()
            return
            if 'invoice' in answer:
                self.set_payment_to_document_debitable(answer.invoice)

    def set_payment_to_document_debitable(self, document):
            class Select_Payment_to_Document_Debitable(Dialog):
                def __init__(self):
                    Dialog.__init__(self)


    @property
    def cfdi(self):
        return self._cfdi

    @cfdi.setter
    def cfdi(self, x):
        self._cfdi = x
        cfdi = self._cfdi
        self.cmb_type.clear()
        if cfdi is not None:
            for k in list(cfdi.keys()):
                if k not in ['uuid', 'type', 'amount', 'total', 'voucher_effect', 'effect']:
                    del cfdi[k]
            if ('voucher_effect' in cfdi and cfdi['voucher_effect'] == 'ingress') or ('effect' in cfdi and cfdi.effect == 'ingress'):
                self.cmb_type.addItems(['bethesda/invoice', 'bethesda/sale_note', 'bethesda/ticket',
                                        'bethesda/remission', 'bethesta/charge_note'])
            elif ('voucher_effect' in cfdi and cfdi['voucher_effect'] == 'egress') or ('effect' in cfdi and cfdi.effect == 'egress'):
                self.cmb_type.addItems(['bethesda/note_credit', 'bethesda/return_note'])
            else:
                self.cmb_type.addItems(ALL_DOCUMENT_TYPE)
        else:
            self.cmb_type.addItems(ALL_DOCUMENT_TYPE)
        self.update_cfdi_ui()

    @property
    def items(self):
        return self.modelitems.datasource

    def update_cfdi_ui(self):
        cfdi = self._cfdi
        if cfdi is not None:
            if 'uuid' in cfdi:
                self.lbl_cfdi_uuid.setText(cfdi['uuid'])
            else:
                self.lbl_cfdi_uuid.setText('')
            if 'total' in cfdi:
                self.lbl_cfdi_total.setText(format_currency(cfdi['total']))
            else:
                self.lbl_cfdi_total.setText('')
            if 'voucher_effect' in cfdi:
                self.lbl_cfdi_voucher_effect.setText(cfdi['voucher_effect'])
            elif 'effect' in cfdi:
                self.lbl_cfdi_voucher_effect.setText(cfdi.effect)
            else:
                self.lbl_cfdi_voucher_effect.setText('')
        else:
            self.lbl_cfdi_uuid.setText('')
            self.lbl_cfdi_voucher_effect.setText('')
            self.lbl_cfdi_total.setText('')

    def update_amount(self, *args):
        self.lbl_amount_items.setText(format_currency(self.modelitems.totalamount()))

    def handle_btn_load_cfdi(self):
        loader = Loader_Cfdi(self)
        loader.exec_()
        if loader.cfdi is not None:
            # first i have to search provider, see if i should put the items and things like that
            cfdi = loader.cfdi
            if 'folio' in cfdi and not self.txt_folio.text:
                self.txt_folio.setText(cfdi['folio'])
            if not self.txt_datetime.text:
                self.txt_datetime.setText(cfdi['datetime'])
            if self.widget_provider.provider is None:
                msg = {'type_message': 'find_one', 'type': 'piper/provider', 'query': {'rfc': cfdi['emitter']['rfc']}}
                answer = self.agent_piper(msg)
                if 'result' in answer and answer['result'] is not None:
                    self.widget_provider.provider = answer['result']
            for item in self.items:
                if 'description' in item and item['description']:
                    break
            else:
                items = list()
                for concept in cfdi['concepts']:
                    item = Dict({'description': concept['description'], 'quanty': concept['quanty']})
                    if 'number_id' in concept:
                        item['sku'] = concept['number_id']
                    elif 'sku' in concept:
                        item['sku'] = concept['sku']

                    if 'price' in concept:
                        item['price'] = concept['price']
                    elif 'value' in concept:
                        item.price = concept.value
                    items.append(item)
                self.modelitems.datasource = items

            if not self.txt_amount.text:
                self.txt_amount.setText(format_currency(cfdi['total']))
            if 'discount' in cfdi and not self.txt_discount.text:
                self.txt_discount.setText(format_currency(cfdi['discount']))

            self.cfdi = cfdi


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Create_Document()
    vv.show()
    sys.exit(app.exec_())
