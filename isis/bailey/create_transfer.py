from isis.dialog import Dialog
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.v_box_layout import V_Box_Layout
from isis.grid_layout import Grid_Layout
from isis.label import Label
from isis.decimal_edit import Decimal_Edit
from isis.group_box import Group_Box
from isis.plain_text_edit import Plain_Text_Edit
from isis.push_button import Push_Button
from decimal import Decimal as D
from isis.check_box import Check_Box
from isis.h_box_layout import H_Box_Layout
from isis.utils import format_currency
from functools import reduce
from isis.event import Event
from PySide2.QtCore import Qt
from isis.line_edit import Line_Edit
from isis.bailey.widget_account import Widget_Account
from isis.bethesda.search_document_purchase import Search_Document_Purchase
from katherine import d1
from dict import Dict as dict, List as list
from utils import find_one
from isis.message_box import Message_Box


class Documents_Model(Table):
    def __init__(self, parent_gui=None):
        Table.__init__(self)
        self.columns.add('id', str)
        self.columns.add('type', str)
        self.columns.add('folio', str)
        self.columns.add('debit', D, 'c')
        self.columns.add('credit', D, 'c')
        self.with_new_empty_row = True

        self.columns['folio'].changing_item_value = self.handle_changing_item_value_folio
        self.columns['debit'].changing_value = self.handle_changing_debit
        self.columns['credit'].changing_value = self.handle_changing_credit
        self.columns['debit'].getter_data = lambda x: x.value if 'value' in x and x.value > 0 else None
        self.columns['credit'].getter_data = lambda x: -x.value if 'value' in x and x.value < 0 else None

        self.columns['type'].readonly = True
        self.columns['debit'].readonly = True
        self.columns['credit'].readonly = True
        self.parent_gui = parent_gui

        self.datasource = list()

        self.new_cfdis_document = Event()

    def handle_changing_item_value_folio(self, item, value):
        if value is not None and value and ('folio' not in item or item.folio != value):
            searcher = Search_Document_Purchase(self.parent_gui)
            result = searcher.search(value)
            if result is not None:
                self.set_item(item, result)
                if 'cfdi' in result and 'uuid' in result.cfdi:
                    self.new_cfdis_document(result.cfdi.uuid)
                return True
            elif len(item):
                item.clear()
                return True
        else:
            return False

    @staticmethod
    def set_item(old, new):
        for k in ['id', 'type', 'folio', 'amount']:
            if k in new:
                old[k] = new[k]
            elif k in old:
                del old[k]

        if 'amount' in old and 'type' in old:
            if old.type in ['bethesda/invoice', 'bethesda/remission', 'bethesda/ticket', 'bethesda/sale_note']:
                old.value = old.amount
            else:
                old.value = -old.amount
            del old.amount
        elif 'amount' in old and 'type' not in old:
            old.value = old.amount
            del old.amount

    def handle_changing_debit(self, i, value):
        doc = self.datasource[i]
        if value is not None and value != 0:
            if 'value' not in doc or doc.value > 0:
                doc.value = value
            elif 'value' in doc and doc.value < 0:
                    doc.value += value
        elif 'value' in doc and doc.value > 0:
            del doc.value
        else:
            return False

    def handle_changing_credit(self, i, value):
        doc = self.datasource[i]
        if value is not None and value != 0:
            if 'value' not in doc or doc.value < 0:
                doc.value = -value
            else:
                    doc.value -= value
        elif 'value' in doc and doc.value < 0:
            del doc.value
        else:
            return False

    @property
    def totalvalue(self):
        return reduce(lambda x, y: x + y.value, filter(lambda x: 'value' in x, self.datasource), 0)


class Cfdis_Model(Table):
    def __init__(self, parent_gui=None):
        Table.__init__(self)
        self.columns.add('uuid', str)
        self.columns.add('folio', str)
        self.columns.add('effect', str)
        self.columns.add('debit', D, 'c')
        self.columns.add('credit', D, 'c')
        self.parent_gui = parent_gui
        self.datasource = list()
        self.columns['debit'].getter_data = lambda x: x.value if x.value > 0 else None
        self.columns['credit'].getter_data = lambda x: -x.value if x.value < 0 else None

        self.columns['effect'].readonly = True
        self.columns['debit'].readonly = True
        self.columns['credit'].readonly = True

    @property
    def totalvalue(self):
        return reduce(lambda x, y: x + y.value, filter(lambda x: 'value' in x, self.datasource), 0)

    def changing_item_value_folio(self, item, value):
        if value is not None and value and ('folio' not in item or item.folio != value):
            result = list(d1.haley.cfdi.find({'uuid': value}))
            if len(result) == 1:
                self.set_cfdi_to_item(item, result)

            elif len(result) > 1:
                pass
            elif len(result) == 0:
                Message_Box.warning(self.parent_gui, 'Error', 'no se encontro cfdi con ese uuid')
                return False

        else:
            return False

    def set_cfdi_to_item(self, item, cfdi):
        for k in ['uuid', 'folio', 'type', 'total', 'effect']:
            if k in cfdi:
                item[k] = cfdi[k]
            elif k in item:
                del item[k]

        if item.effect not in ['ingress', 'egress']:
            Message_Box.warning(self.parent_gui, 'Error', 'el cfdi debe de ser de efecto ingreso o egreso')
            return
        if item.effect == 'ingress':
            item.value = item.total
        else:
            item.value = -item.total
        del item.total

    def add_cfdi(self, cfdi, parent_gui=None):
        item = dict()
        if find_one(lambda x: x.uuid == cfdi.uuid, self.datasource) is None:
            self.set_cfdi_to_item(item, cfdi)
            self.add_row(item)
        elif parent_gui is not None:
            Message_Box.warning(parent_gui, 'Error', 'Ya se encuentra el cfdi agragado')

    def changing_item_value_uuid(self, item, value):
        if value is not None and value and ('uuid' not in item or item.uuid != value):
            cfdi = d1.haley.cfdi.find_one({'uuid': value})

        else:
            return False


class Table_View_Documents(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)
        self.enable_delete_row_with_supr = True


class Table_View_Cfdis(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)
        self.enable_delete_row_with_supr = True


class Dialog_Documents(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 500)
        self.window_title = 'Documents'

        btn_add_documents_beneficiary = Push_Button('Agregar de documentos de beneficiario', self)
        self.table = Table_View()
        self.table.enable_delete_row_with_supr = True
        lbl_total = Label('Total: ', self)
        self.lbl_total = Label(self)

        lbl_total.fix_size_based_on_font()

        self._model = Documents_Model(parent_gui=self)
        self.table.model = self.model

        main_layout = V_Box_Layout()
        main_layout.addWidget(btn_add_documents_beneficiary)
        main_layout.addWidget(self.table)
        total_layout = H_Box_Layout()
        total_layout.addWidget(lbl_total)
        total_layout.addWidget(self.lbl_total)
        main_layout.addLayout(total_layout)
        self.layout = main_layout

        self.model.any_change_in_datasource.suscribe(self.update_total)
        self.update_total()

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self.model.parent_gui = self
        self._model = model
        self.table.model = model
        self.model.any_change_in_datasource.suscribe(self.update_total)

    def update_total(self, *args):
        self.lbl_total.text = format_currency(self.model.totalvalue)

    def account_destination_changed(self, account):
        pass

    @property
    def documents(self):
        return self.model.datasource

    @documents.setter
    def documents(self, documents):
        self.model.datasource = documents


class Dialog_Cfdis(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 500)
        self.window_title = 'Cfdis'
        self.table = Table_View_Cfdis(self)
        self._model = None
        self.model = Cfdis_Model(parent_gui=True)
        self.table.model = self.model
        lbl_total = Label('Total: ', self)
        self.lbl_total = Label(self)

        lbl_total.fix_size_based_on_font()

        layout_main = V_Box_Layout(self)
        layout_main.addWidget(self.table)
        layout_total = H_Box_Layout()
        layout_total.addWidget(lbl_total)
        layout_total.addWidget(self.lbl_total)
        layout_main.addLayout(layout_total)
        self.layout = layout_main

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        model.parent_gui = self
        self._model = model
        self.table.model = model
        self.model.any_change_in_datasource.suscribe(self.updatetotal)

    def updatetotal(self, *args):
        self.lbl_total.text = format_currency(reduce(lambda x, y: x + y.value,
                                                     filter(lambda x: 'value' in x, self.model.datasource), 0))

    def account_destination_changed(self, account):
        pass


class Create_Transfer(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500,550)
        self.setWindowTitle(self.__class__.__name__)
        self.widgetaccountorigen = Widget_Account(self)
        self.widgetaccountdestination = Widget_Account(self)
        self.widgetaccountorigen.with_change_button = True
        self.widgetaccountdestination.with_change_button = True
        self.widgetaccountorigen.label = 'Origen'
        self.widgetaccountdestination.label = 'Destination'

        lbl_datetime = Label('datetime: ', self)
        lbl_amount = Label('amount: ', self)

        self.txt_datetime = Line_Edit(self)
        self.decimal_amount = Decimal_Edit(self)

        btn_add_from_debts = Push_Button('Add from debts', self)
        btn_search_by_folio = Push_Button('Buscar por folio', self)
        self.chk_documents = Check_Box('Documents', self)
        self.chk_cfdis = Check_Box('Cfdis', self)

        lbl_datetime.fix_size_based_on_font()
        lbl_amount.fix_size_based_on_font()

        self.decimal_amount.setMaximum(1000000)
        self.decimal_amount.setMinimum(0)
        self.decimal_amount.setPrefix('$')
        # self.decimal_amount.value = 63369.21

        tx_gbox = Group_Box(self)
        tx_gbox.label = Label('tx', tx_gbox)
        lbl_tx_description = Label('description: ', self)
        lbl_tx_number = Label('number: ', self)
        lbl_tx_description.fix_size_based_on_font()
        lbl_tx_number.fix_size_based_on_font()
        self.txt_tx_description = Plain_Text_Edit(tx_gbox)
        self.txt_tx_number = Line_Edit(tx_gbox)

        m = self.txt_tx_description.fontMetrics()
        cm = self.txt_tx_description.contentsMargins()
        self.txt_tx_description.setFixedHeight(m.lineSpacing() * 3)

        self.spn_sum = Decimal_Edit(self)
        self.btn_use_sum = Push_Button('use', self)

        btn_create = Push_Button('create', self)
        btn_close = Push_Button('close', self)

        layout_main = V_Box_Layout(self)
        layout_main.addWidget(self.widgetaccountorigen)
        layout_main.addWidget(self.widgetaccountdestination)
        layout_controls = Grid_Layout()
        layout_controls.addWidget(lbl_datetime, 0, 0)
        layout_controls.addWidget(self.txt_datetime, 0, 1)
        layout_controls.addWidget(lbl_amount, 1, 0)
        layout_controls.addWidget(self.decimal_amount, 1, 1)
        layout_buttons = H_Box_Layout()
        layout_buttons.addWidget(btn_add_from_debts)
        layout_buttons.addWidget(btn_search_by_folio)
        layout_controls.addLayout(layout_buttons, 2, 0, 1, -1)
        layout_main.addLayout(layout_controls)
        layout_chks = H_Box_Layout()
        layout_chks.addWidget(self.chk_documents)
        layout_chks.addWidget(self.chk_cfdis)
        layout_main.addLayout(layout_chks)
        layout_tx = Grid_Layout(tx_gbox)
        layout_tx.addWidget(tx_gbox.label, 0, 0)
        layout_tx.addWidget(lbl_tx_number, 1, 0)
        layout_tx.addWidget(self.txt_tx_number, 1, 1)
        layout_tx.addWidget(lbl_tx_description, 2, 0)
        layout_tx.addWidget(self.txt_tx_description, 2, 1, 1, -1)
        layout_main.addWidget(tx_gbox)
        layout_main.addStretch()
        buttons_layout = Grid_Layout()
        buttons_layout.addWidget(self.spn_sum, 0, 0)
        buttons_layout.addWidget(self.btn_use_sum, 0, 1)
        buttons_layout.addWidget(btn_create, 0, 2)
        buttons_layout.addWidget(btn_close, 0, 3)
        layout_main.addLayout(buttons_layout)

        self.layout = layout_main

        self.decimal_amount.value_changed.suscribe(self.handle_decimal_amount_value_changed)

        # from katherine import d1
        # self.widgetaccountorigen.account = d1.bailey.account.find_one({'id': '35-3'}, {'_id': False})
        # self.widgetaccountdestination.account = d1.bailey.account.find_one({'id': '35-15'}, {'_id': False})
        self.chk_documents.stateChanged.connect(self.handle_chk_documents_state_changed)
        self.chk_cfdis.stateChanged.connect(self.handle_chk_cfdis_state_changed)
        self.dialog_documents = None
        self.dialog_cfdis = None

        self.model_documents = Documents_Model(parent_gui=self)
        self.model_cfdis = Cfdis_Model(parent_gui=self)

    def add_cfdi(self, cfdi):
        if isinstance(cfdi, str):
            cfdi = d1.haley.cfdi.find_one({'uuid': cfdi}, {'_id': False})
        elif isinstance(cfdi, dict) and not len(cfdi) > 2:
            cfdi = d1.haley.cfdi.find_one({'uuid': cfdi.uuid}, {'_id': False})
        if find_one(lambda x: x.uuid == cfdi.uuid, self.cfdis) is None:
            if cfdi.effect not in ['ingress', 'egress']:
                Message_Box.warning(self, 'Error', 'cfdi shoulb be [\'ingress\', \'egress\'] not ' + cfdi.effect)
                return False
            self.model_cfdis.add_cfdi(cfdi)

    @property
    def cfdis(self):
        return self.model_cfdis.datasource

    def handle_chk_documents_state_changed(self, state):
        if state == Qt.Checked:
            if self.dialog_documents is None:
                self.dialog_documents = Dialog_Documents(self)
                self.dialog_documents.model = self.model_documents
                self.widgetaccountdestination.account_changed.suscribe(self.dialog_documents.account_destination_changed)
                self.dialog_documents.closed.suscribe(lambda: self.chk_documents.setCheckState(Qt.Unchecked))
                self.dialog_documents.model.new_cfdis_document.suscribe(self.add_cfdi)
            self.dialog_documents.show()
        else:
            if self.dialog_documents is not None:
                self.dialog_documents.hide()

    def handle_chk_cfdis_state_changed(self, state):
        if state == Qt.Checked:
            if self.dialog_cfdis is None:
                self.dialog_cfdis = Dialog_Cfdis(self)
                self.dialog_cfdis.model = self.model_cfdis
                self.widgetaccountdestination.account_changed.suscribe(self.dialog_cfdis.account_destination_changed)
                self.dialog_cfdis.closed.suscribe(lambda: self.chk_cfdis.setCheckState(Qt.Unchecked))
            self.dialog_cfdis.show()
        else:
            if self.dialog_cfdis is not None:
                self.dialog_cfdis.hide()

    def handle_decimal_amount_value_changed(self, value):
        pass


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Create_Transfer()
    vv.show()
    sys.exit(app.exec_())
