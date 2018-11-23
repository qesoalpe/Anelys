from isis.dialog_select_table import Dialog_Select_Table
from isis.data_model.table import Table
from decimal import Decimal as D


class Select_Cfdi_No_Attached(Dialog_Select_Table):
    def __init__(self, parent=None):
        Dialog_Select_Table.__init__(self, parent)
        self.resize(1200, 500)
        self.setWindowTitle('Select_Cfdi_No_Attached')
        # self.tableview.installEventFilter(self)

    @staticmethod
    def getter_data_emitter(row):
        emitter = row.emitter
        if 'name' in emitter:
            return emitter.name
        elif 'rfc' in emitter:
            return emitter.rfc

    def loading(self, e):
        from sarah.acp_bson import Client
        agent_cfdi = Client('isis.haley.select_cfdi_no_attached', 'haley')
        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'haley/cfdis_no_attached'}
        answer = agent_cfdi(msg)
        e['list'] = answer['result']
        e['list'].sort(key=lambda x: x.datetime + x.folio if 'folio' in x else '', reverse=True)
        table = Table()
        e['table'] = table
        table.columns.add('folio', str)
        table.columns.add('datetime', str)
        table.columns.add('effect', str)
        table.columns.add('emitter', str)
        table.columns.add('total', D, 'c')
        table.columns.add('uuid', str)
        table.datasource = e.list

        table.columns['folio'].getter_data = ['folio', 'voucher_effect']
        table.columns['emitter'].getter_data = self.getter_data_emitter

    # def eventFilter(self, obj, event):
    #     from PySide.QtCore import QEvent, Qt
    #     from PySide.QtGui import QMouseEvent, QMenu
    #     if obj is self.tableview:
    #         if event.type() == QEvent.ContextMenu:
    #             index = self.tableview.indexAt(event.pos())
    #             if index.isValid():
    #                 item = self.selectablelist[index.row()]
    #                 print(item['folio'] if 'folio' in item else item['uuid'])
    #                 menu = QMenu(self.tableview)
    #                 menu.addAction('action')
    #                 menu.popup(event.globalPos())
    #                 return True
    #     return False

