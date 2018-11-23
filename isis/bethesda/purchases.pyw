from PySide.QtGui import *
from PySide.QtCore import Qt
from isis.data_model.table import Table
from dict import Dict
from isis.utils import format_currency
from isis.main_window import Main_Window
from isis.dialog import Dialog
from isis.table_view import Table_View
from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
from decimal import Decimal
from copy import deepcopy


class Documents_Model(Table):
    def __init__(self):
        Table.__init__(self, 'Documents')
        self.columns.add('id', str)
        self.columns.add('folio', str)
        self.columns.add('type', str)
        self.columns.add('value', Decimal, 'c')
        self.olders = None
        self.readonly = True


class Edit_Documents(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 400)
        self.setWindowTitle('Edit_Documents')
        self.tableview = Table_View()
        self.model = Documents_Model()
        self.tableview.model = self.model
        btn_add_document = QPushButton('add_document', self)
        btn_close = QPushButton('close', self)

        mainlayout = QHBoxLayout(self)
        mainlayout.addWidget(self.tableview)
        buttonslayout = QVBoxLayout()
        buttonslayout.addWidget(btn_add_document)
        buttonslayout.addWidget(btn_close)
        buttonslayout.addStretch()
        mainlayout.addLayout(buttonslayout)
        self.setLayout(mainlayout)
        self._purchase = None
        btn_add_document.clicked.connect(self.handle_btn_add_document_clicked)
        btn_close.clicked.connect(self.close)
        self.olders = None

    def handle_btn_add_document_clicked(self):
        from isis.bethesda.select_document_purchase_without_purchase import Select_Document_Purchase_Without_Purchase
        dialog = Select_Document_Purchase_Without_Purchase(self, self.purchase.provider)
        dialog.exec_()
        if dialog.selected is not None:
            from sarah.acp_bson import Client
            agent_bethesda = Client('', 'bethesda')
            document = dialog.selected
            for k in list(document.keys()):
                if k not in ['id', 'folio', 'type']:
                    del document[k]
            msg = {'type_message': 'action', 'action': 'bethesda/attach_document', 'purchase': {'id': self.purchase.id},
                   'document': document}
            answer = agent_bethesda(msg)
            if 'error' not in answer or not answer.error:
                self.model.add_row(deepcopy(document))
                if 'document' in self.purchase:
                    self.purchase.documents = [self.purchase.document, document]
                    del self.purchase.document
                elif 'documents' in self.purchase:
                    self.purchase.documents.append(document)
                else:
                    self.purchase.document = document

    @property
    def purchase(self):
        return self._purchase

    @purchase.setter
    def purchase(self, purchase):
        self._purchase = purchase
        if purchase is not None:
            if 'document' in purchase:
                documents = [deepcopy(purchase.document)]
            elif 'documents' in purchase:
                documents = deepcopy(purchase.documents)
            else:
                documents = list()
            self.olders = [doc.id for doc in documents]
            self.model.olders = self.olders
            self.model.datasource = documents
        else:
            self.olders = list()
            self.model.olders = list()
            self.model.datasource = None


class Purchases_Table_Model(Table):
    def __init__(self):
        Table.__init__(self, 'purchases')
        self.columns.add('id', str)
        self.columns.add('datetime', str)
        self.columns.add('provider', str)
        self.columns.add('total', str)
        self.readonly = True

        def ff(row):
            if 'amount' in row:
                return format_currency(row.amount)
            elif 'total' in row:
                return format_currency(row.total)
            else:
                return ''

        self.columns['total'].getter_data = ff

        def ff(row):
            if 'provider' in row:
                provider = row.provider
                if 'business_name' in provider:
                    return provider.business_name
                elif 'name' in provider:
                    return provider.name
                else:
                    return ''
            else:
                return ''
        self.columns['provider'].getter_data = ff


class Table_View_Purchases(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = QMenu(self)
                action_edit_documents = menu.addAction('editar documentos')
                def ff():
                    editer = Edit_Documents(self)
                    editer.purchase = self.model.datasource[index.row()]
                    editer.show()
                action_edit_documents.triggered.connect(ff)
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class Purchases(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(800, 600)
        self.setWindowTitle('Purchases')
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        self.widgetprovider = Widget_Viewer_Provider(self.cwidget)
        self.tableview = Table_View_Purchases(self.cwidget)
        self.purchasesmodel = Purchases_Table_Model()
        self.tableview.model = self.purchasesmodel

        layoutmain = QVBoxLayout(self.cwidget)
        layoutmain.addWidget(self.widgetprovider)
        layoutmain.addWidget(self.tableview)
        self.cwidget.setLayout(layoutmain)

        from pymongo import MongoClient
        d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
        d1.admin.authenticate('alejandro', '47exI4')

        cursor = d1.bethesda.purchase.find({}, {'_id': False}).limit(50).sort('datetime', -1)
        self.purchases = [purchase for purchase in cursor]

        self.widgetprovider.with_button_change = True
        self.widgetprovider.with_button_quit = True

        def hh(provider):
            if provider is None:
                filter = {}
            else:
                filter = {'provider.id': provider.id}

            cursor = d1.bethesda.purchase.find(filter, {'_id': False}).limit(50).sort('datetime', -1)
            self.purchases = [purchase for purchase in cursor]

        self.widgetprovider.provider_changed.suscribe(hh)

    @property
    def purchases(self):
        return self.purchasesmodel.datasource

    @purchases.setter
    def purchases(self, purchases):
        self.purchasesmodel.datasource = purchases


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Purchases()
    vv.show()
    sys.exit(app.exec_())
