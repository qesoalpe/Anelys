from isis.data_model.table import Table
from sarah.acp_bson import Client
from isis.main_window import Main_Window
from isis.label import Label
from decimal import Decimal as D
from isis.table_view import Table_View


class Payments_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('type', str)
        self.columns.add('value', D, 'c')
        self.readonly = True


class Payments_Table_View(Table_View):
    pass


class Register_Payment(QDialog):
    class Select_Origen(QDialog):
        def __init__(self, parent):
            QDialog.__init__(self, parent)
            btn_from_bethesda_document_creditable = Push_Button('bethesda/document_creditable', self)
            btn_from_vasya_receipt = Push_Button('vasya/receipt', self)
            btn_from_bethesda_descuadre = Push_Button('bethesda/descuadre', self)
            btn_from_piper_debt = Push_Button('piper/debt', self)
            layoutmain = QVBoxLayout(self)
            layoutmain.addWidget(btn_from_bethesda_document_creditable)
            layoutmain.addWidget(btn_from_vasya_receipt)
            layoutmain.addWidget(btn_from_bethesda_descuadre)
            layoutmain.addWidget(btn_from_piper_debt)

            self.from_ = None

            def handler_1():
                self.from_ = 'betheda/document_creditable'
                self.close()

            def handler_2():
                self.from_ = 'vasya/receipt'
                self.close()

            def handler_3():
                self.from_ = 'bethesda/descuadre'
                self.close()

            def handler_4():
                self.from_ = 'piper/debt'
                self.close()

            btn_from_bethesda_document_creditable.clicked.connect(handler_1)
            btn_from_vasya_receipt.clicked.connect(handler_2)
            btn_from_bethesda_descuadre.clicked.connect(handler_3)
            btn_from_piper_debt.clicked.connect(handler_4)

            self.setLayout(layoutmain)

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        lbl_type = Label('type: ', self)
        lbl_folio = Label('folio: ', self)
        lbl_amount = Label('amount: ', self)
        lbl_provider = Label('provider: ', self)
        lbl_datetime = Label('datetime: ', self)

        self.lbl_type = Label(self)
        self.lbl_folio = Label(self)
        self.lbl_amount = Label(self)
        self.lbl_provider = Label(self)
        self.lbl_datetime = Label(self)

        self.tableview = Table_Payments(self)
        btn_add_payment = Push_Button('+', self)
        btn_add_payment.setFixedSize(25, 25)
        setfixedwidth(lbl_type)
        setfixedwidth(lbl_folio)
        setfixedwidth(lbl_amount)
        setfixedwidth(lbl_provider)
        setfixedwidth(lbl_datetime)

        layoutmain = QGridLayout(self)
        layoutmain.addWidget(lbl_type, 0, 0)
        layoutmain.addWidget(self.lbl_type, 0, 1)
        layoutmain.addWidget(lbl_folio, 0, 2)
        layoutmain.addWidget(self.lbl_folio, 0, 3)
        layoutmain.addWidget(lbl_amount, 1, 0)
        layoutmain.addWidget(self.lbl_amount, 1, 1)
        layoutmain.addWidget(lbl_datetime, 1, 2)
        layoutmain.addWidget(self.lbl_datetime, 1, 3)
        layoutmain.addWidget(lbl_provider, 2, 0)
        layoutmain.addWidget(self.lbl_provider, 2, 1, 1, -1)

        layouttable = QHBoxLayout()
        layoutbuttonstable = QVBoxLayout()
        layoutbuttonstable.addWidget(btn_add_payment)
        layoutbuttonstable.addStretch()
        layouttable.addWidget(self.tableview)
        layouttable.addItem(layoutbuttonstable)
        layoutmain.addItem(layouttable, 3, 0, 1, -1)

        self.modelpayments = Model_Payments(self)
        self.tableview.setModel(self.modelpayments)

        btn_add_payment.clicked.connect(self.handle_button_add_payment_clicked)

        self.setLayout(layoutmain)
        self._document = None

    def handle_button_add_payment_clicked(self):
        vv = self.Select_Origen(self)
        vv.exec_()
        if vv.from_ is not None:
            if vv.from_ == 'piper/debt':
                if 'amount' in self.document:
                    maximum = self.document['amount']
                elif 'total' in self.document:
                    maximum = self.document['total']
                default = maximum
                debt_value, ok = QInputDialog.getDouble(self, 'debt', 'put debt\'s amount', default, 0, maximum, 2)
            elif vv.from_ == 'vasya/receipt':
                class Select(QDialog):
                    def __init__(self, parent):
                        QDialog.__init__(self, parent)
                        btn_create = Push_Button('create', self)
                        btn_choose = Push_Button('choose', self)
                        layoutmain = QVBoxLayout(self)
                        layoutmain.addWidget(btn_create)
                        layoutmain.addWidget(btn_choose)
                        self.selected = None

                        def handle_1():
                            self.selected = 'create'
                            self.close()

                        def handle_2():
                            self.selected = 'choose'
                            self.close()

                        btn_create.clicked.connect(handle_1)
                        btn_choose.clicked.connect(handle_2)

                selecter = Select(self)
                selecter.exec_()
                if selecter.selected is not None:
                    if selecter.selected == 'create':
                        print('hanlde create')
                    elif selecter.selected =='choose':
                        print('handle choose')

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, x):
        self._document = x
        doc = x
        if doc is not None:
            if 'folio' in doc:
                self.lbl_folio.setText(doc['folio'])
            else:
                self.lbl_folio.setText('')
            if 'type' in doc:
                self.lbl_type.setText(doc['type'])
            else:
                self.lbl_type.setText('')
            if 'amount' in doc:
                self.lbl_amount.setText(format_currency(doc['amount'], 'MXN', locale='es_mx'))
            elif 'total' in doc:
                self.lbl_amount.setText(format_currency(doc['total'], 'MXN', locale='es_mx'))
            else:
                self.lbl_amount.setText('')
            if 'datetime' in doc:
                self.lbl_datetime.setText(doc['datetime'])
            elif 'date' in doc:
                self.lbl_datetime.setText(doc['date'])
            else:
                self.lbl_datetime.setText('')
            if 'provider' in doc:
                provider = doc['provider']
                if isinstance(provider, str):
                    self.lbl_provider.setText(provider)
                elif isinstance(provider, dict):
                    if 'business_name' in provider:
                        self.lbl_provider.setText(provider['business_name'])
                    elif 'name' in provider:
                        self.lbl_provider.setText(provider['name'])
                    elif 'rfc' in provider:
                        self.lbl_provider.setText(provider['rfc'])
                    elif 'id' in provider:
                        self.lbl_provider.setText(provider['id'])
                    else:
                        self.lbl_provider.setText('')
            else:
                self.lbl_provider.setText('')
        else:
            self.lbl_type.setText('')
            self.lbl_folio.setText('')
            self.lbl_amount.setText('')
            self.lbl_datetime.setText('')
            self.lbl_provider.setText('')


class Model_Documents(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._datasource = None

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def rowCount(self, parent=None):
        if self._datasource is not None and isinstance(self._datasource, list):
            return len(self._datasource)
        else:
            return 0

    def columnCount(self, parent=None):
        return 7

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.COLUMN_ID:
                return 'id'
            elif section == self.COLUMN_TYPE:
                return 'type'
            elif section == self.COLUMN_FOLIO:
                return 'folio'
            elif section == self.COLUMN_DATETIME:
                return 'datetime'
            elif section == self.COLUMN_PROVIDER:
                return 'provider'
            elif section == self.COLUMN_AMOUNT:
                return 'amount'
            elif section == self.COLUMN_LABELS:
                return 'labels'

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self.datasource[index.row()]
            if index.column() == self.COLUMN_ID:
                if 'id' in data:
                    return data['id']
            elif index.column() == self.COLUMN_TYPE:
                if 'type' in data:
                    return data['type']
            elif index.column() == self.COLUMN_FOLIO:
                if 'folio' in data:
                    return data['folio']
            elif index.column() == self.COLUMN_DATETIME:
                if 'datetime' in data:
                    return data['datetime']
                elif 'date' in data:
                    return data['date']
            elif index.column() == self.COLUMN_PROVIDER:
                if 'provider' in data:
                    provider = data['provider']
                    if isinstance(provider, str):
                        return provider
                    elif isinstance(provider, dict):
                        if 'business_name' in provider:
                            return provider['business_name']
                        elif 'name' in provider:
                            return provider['name']
                        elif 'id' in provider:
                            return provider['id']
            elif index.column() == self.COLUMN_AMOUNT:
                if 'amount' in data:
                    return format_currency(data['amount'], 'MXN', locale='es_mx')
                elif 'total' in data:
                    return format_currency(data['total'], 'MXN', locale='es_mx')
            elif index.column() == self.COLUMN_LABELS:
                if 'labels' in data:
                    labels = data['labels']
                    if isinstance(labels, list):
                        return json.dumps(labels)
                    elif isinstance(labels, str):
                        return labels

    COLUMN_ID = 0
    COLUMN_TYPE = 1
    COLUMN_FOLIO = 2
    COLUMN_DATETIME = 3
    COLUMN_PROVIDER = 4
    COLUMN_AMOUNT = 5
    COLUMN_LABELS = 6


class Table_View_Documents(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)

    def setModel(self, model):
        QTableView.setModel(self, model)

        def aa():
            self.resizeColumnsToContents()

        model.modelReset.connect(aa)
        model.dataChanged.connect(aa)
        model.rowsInserted.connect(aa)
        model.rowsRemoved.connect(aa)
        aa()

    def mousePressEvent(self, event):
        QTableView.mousePressEvent(self, event)
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = QMenu(self)
                action = menu.addAction('register payment')
                def hh():
                    vv = Register_Payment(self)
                    vv.document = self.model().datasource[index.row()]
                    vv.show()
                action.triggered.connect(hh)
                menu.popup(event.globalPos())


class Documents(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 500)
        self.setWindowTitle('Documents')
        self.setWindowState(self.windowState() | Qt.WindowMaximized)
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        layout_main = QVBoxLayout(self.cwidget)

        self.tableview = Table_View_Documents(self.cwidget)

        layout_main.addWidget(self.tableview)

        self.modeldocuments = Model_Documents(self.cwidget)

        self.tableview.setModel(self.modeldocuments)

        self._documents = None

        self.agent_bethesda = Client('Documents', 'bethesda')
        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'bethesda/document_debitable_without_payment'}
        answer = self.agent_bethesda(msg)
        self.documents = answer['result']

    @property
    def documents(self):
        return self._documents

    @documents.setter
    def documents(self, x):
        self._documents = x
        self.modeldocuments.datasource = x


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Documents()
    vv.show()
    sys.exit(app.exec_())
