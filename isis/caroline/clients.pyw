from PySide.QtGui import *
from PySide.QtCore import *
from sarah.acp_bson import Client
import json
from decimal import Decimal
from isis.reina.search_person import Search_Person
from isis.reina.search_corporation import Search_Corporation


class Dialog_Create_From(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        label = QLabel('Select from where create the client', self)
        btn_from_reina_person = QPushButton('from reina/person', self)
        btn_from_reina_corporation = QPushButton('from reina/corporation', self)
        mainlayout = QVBoxLayout(self)
        mainlayout.addWidget(label)
        mainlayout.addWidget(btn_from_reina_person)
        mainlayout.addWidget(btn_from_reina_corporation)
        self.setLayout(mainlayout)
        self.create_from = None
        btn_from_reina_person.clicked.connect(self.handle_btn_from_reina_person_clicked)
        btn_from_reina_corporation.clicked.connect(self.handle_btn_from_reina_corporation_clicked)

    def handle_btn_from_reina_person_clicked(self):
        self.create_from = 'reina/person'
        self.close()

    def handle_btn_from_reina_corporation_clicked(self):
        self.create_from = 'reina/corporation'
        self.close()


def setfixedwidth(ww):
    ww.setFixedWidth(ww.fontMetrics().width(ww.text()))


class Viewer_Client(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.resize(500, 350)
        self.setWindowTitle('Viewer_Client')
        self.txt_client = QTextEdit(self)
        self.txt_client.setReadOnly(True)
        layoutmain = QVBoxLayout(self)
        layoutmain.addWidget(self.txt_client)
        self.setLayout(layoutmain)
        self._client = None

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, x):
        self._client = x
        self.update_ui()

    def update_ui(self):
        client = self._client
        if client is None:
            self.txt_client.setText('')
        else:
            self.txt_client.setText(json.dumps(client, indent=2))


class Editor_Client(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.resize(500, 350)
        self.setWindowTitle('Editor_Client')
        self.txt_client = QTextEdit(self)
        btn_save = QPushButton('save', self)
        btn_close = QPushButton('close', self)

        layoutmain = QVBoxLayout(self)
        layoutmain.addWidget(self.txt_client)

        buttonslayout = QHBoxLayout()
        buttonslayout.addStretch()
        buttonslayout.addWidget(btn_save)
        buttonslayout.addWidget(btn_close)
        layoutmain.addItem(buttonslayout)
        self._client = None

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, x):
        self._client = x
        self.update_ui()

    def update_ui(self):
        client = self._client
        if client is None:
            self.txt_client.setText('')
        else:
            self.txt_client.setText(json.dumps(client, indent=2))


class Granter_Credit(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        lbl_client = QLabel('client', self)
        lbl_client_id = QLabel('id: ', self)
        lbl_client_type = QLabel('type: ', self)
        lbl_client_client_type = QLabel('client_type: ', self)
        lbl_client_name = QLabel('name: ', self)
        self.lbl_client_id = QLabel(self)
        self.lbl_client_type = QLabel(self)
        self.lbl_client_client_type = QLabel(self)
        self.lbl_client_name = QLabel(self)

        lbl_credit = QLabel('credit', self)
        lbl_credit_period = QLabel('credit_period: ', self)
        lbl_credit_limit = QLabel('credit_limit: ', self)
        self.txt_credit_period = QLineEdit(self)
        self.spn_credit_limit = QDoubleSpinBox(self)
        self.spn_credit_limit.setPrefix('$')
        self.spn_credit_limit.setMinimum(0)
        self.spn_credit_limit.setMaximum(1000000)
        btn_grant = QPushButton('grant', self)
        btn_close = QPushButton('close', self)
        setfixedwidth(lbl_client)
        setfixedwidth(lbl_client_id)
        setfixedwidth(lbl_client_type)
        setfixedwidth(lbl_client_client_type)
        setfixedwidth(lbl_client_name)
        setfixedwidth(lbl_credit_period)
        setfixedwidth(lbl_credit_limit)

        layoutmain = QGridLayout(self)
        layoutmain.addWidget(lbl_client, 0, 0)
        layoutmain.addWidget(lbl_client_id, 1, 0)
        layoutmain.addWidget(self.lbl_client_id, 1, 1)
        layoutmain.addWidget(lbl_client_type, 2, 0)
        layoutmain.addWidget(self.lbl_client_type, 2, 1)
        layoutmain.addWidget(lbl_client_client_type, 3, 0)
        layoutmain.addWidget(self.lbl_client_client_type, 3, 1)
        layoutmain.addWidget(lbl_client_name, 4, 0)
        layoutmain.addWidget(self.lbl_client_name, 4, 1)
        layoutmain.addWidget(lbl_credit, 5, 0)
        layoutmain.addWidget(lbl_credit_period, 6, 0)
        layoutmain.addWidget(self.txt_credit_period, 6, 1)
        layoutmain.addWidget(lbl_credit_limit, 7, 0)
        layoutmain.addWidget(self.spn_credit_limit, 7, 1)
        buttonslayout = QHBoxLayout()
        buttonslayout.addWidget(btn_grant)
        buttonslayout.addWidget(btn_close)
        layoutmain.addItem(buttonslayout, 8, 0, 1, -1)
        self.setLayout(layoutmain)
        self._client = None
        btn_grant.clicked.connect(self.handle_btn_grant_clicked)
        btn_close.clicked.connect(self.close)
        self.agent_caroline = None

    def handle_btn_grant_clicked(self):
        msg = {'type_message': 'action', 'action': 'caroline/grant_credit', 'client': self.client,
               'credit_limit': Decimal(self.spn_credit_limit.value()), 'credit_period': self.txt_credit_period.text()}
        answer = self.agent_caroline(msg)
        if 'error' in answer or 'account' not in answer:
            QMessageBox.warning(self, 'error', 'an error has happened')
        else:
            QMessageBox.information(self, 'success', 'credito a sido otorgado')
            self.client['account'] = answer['account']
            self.close()

    def update_client_ui(self):
        client = self._client
        if client is not None:
            if 'id' in client:
                self.lbl_client_id.setText(client['id'])
            else:
                self.lbl_client_id.setText('')
            if 'type' in client:
                self.lbl_client_type.setText(client['type'])
            else:
                self.lbl_client_type.setText('')
            if 'client_type' in client:
                self.lbl_client_client_type.setText(client['client_type'])
            else:
                self.lbl_client_client_type.setText('')
            if 'name' in client:
                self.lbl_client_name.setText(client['name'])
            else:
                self.lbl_client_name.setText('')
        else:
            self.lbl_client_id.setText('')
            self.lbl_client_type.setText('')
            self.lbl_client_client_type.setText('')
            self.lbl_client_name.setText('')

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, x):
        self._client = x
        self.update_client_ui()


class Table_Model_Clients(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self._datasource = None

    @property
    def datasource(self):
        return self._datasource

    @datasource.setter
    def datasource(self, x):
        self._datasource = x
        self.modelReset.emit()

    def rowCount(self, parent=None):
        if self._datasource is None:
            return 0
        else:
            return len(self._datasource)

    def columnCount(self, parent=None):
        return 5

    def data(self, index, role):
        if role == Qt.DisplayRole:
            data = self._datasource[index.row()]
            if index.column() == self.COLUMN_ID:
                if 'id' in data:
                    return data['id']
            elif index.column() == self.COLUMN_TYPE:
                if 'type' in data:
                    return data['type']

            elif index.column() == self.COLUMN_CLIENT_TYPE:
                if 'client_type' in data:
                    return data['client_type']
            elif index.column() == self.COLUMN_NAME:
                if 'name' in data:
                    return data['name']
            elif index.column() == self.COLUMN_RFC:
                if 'rfc' in data:
                    return data['rfc']

    def headerData(self, section, horientation, role):
        if horientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == self.COLUMN_ID:
                return 'id'
            elif section == self.COLUMN_TYPE:
                return 'type'
            elif section == self.COLUMN_CLIENT_TYPE:
                return 'client_type'
            elif section == self.COLUMN_NAME:
                return 'name'
            elif section == self.COLUMN_RFC:
                return 'rfc'
    COLUMN_ID = 0
    COLUMN_TYPE = 1
    COLUMN_CLIENT_TYPE = 2
    COLUMN_NAME = 3
    COLUMN_RFC = 4

    def client_updated(self, i):
        topleft = self.index(i, 0)
        bottomrigth = self.index(i, self.columnCount() - 1)
        self.dataChanged.emit(topleft, bottomrigth)

    def insert_client(self, index=None, client=None):
        if index is None:
            index = len(self._datasource)
        if client is None:
            client = dict()
        self.beginInsertRows(QModelIndex(), index, index)
        self._datasource.insert(index, client)
        self.endInsertRows()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


class Table_View_Clients(QTableView):
    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.handler_view = None
        self.handler_edit = None
        self.handler_grant_credit = None
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

    def mousePressEvent(self, event):
        QTableView.mousePressEvent(self, event)
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                menu = QMenu(self)
                view = menu.addAction('view')
                edit = menu.addAction('edit')
                grant_credit = menu.addAction('grant credit')

                def handle_view():
                    if self.handler_view is not None:
                        self.handler_view(index.row())

                def handle_edit():
                    if self.handler_edit is not None:
                        self.handler_edit(index.row())

                def handle_grant_credit():
                    if self.handler_grant_credit is not None:
                        self.handler_grant_credit(index.row())
                view.triggered.connect(handle_view)
                edit.triggered.connect(handle_edit)
                grant_credit.triggered.connect(handle_grant_credit)
                menu.popup(event.globalPos())

    def handle_mode_dataChanged(self, uno=None, dos=None, tres=None):
        self.resizeColumnsToContents()

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.dataChanged.connect(self.handle_mode_dataChanged)
        model.rowsInserted.connect(self.handle_mode_dataChanged)
        model.rowsRemoved.connect(self.handle_mode_dataChanged)
        model.modelReset.connect(self.resizeColumnsToContents)


class Central_Widget(QWidget):
    def __init__(self, parent, agent_caroline=None):
        QWidget.__init__(self, parent)

        btn_create = QPushButton('create', self)
        btn_edit = QPushButton('edit', self)
        btn_view = QPushButton('view', self)
        btn_refresh = QPushButton('refresh', self)
        self.tablemodelclients = Table_Model_Clients()
        self.tableviewclients = Table_View_Clients(self)
        self.tableviewclients.setModel(self.tablemodelclients)
        # self.tablemodelclients.modelReset.connect(self.tableviewclients.resizeColumnsToContents)

        buttonslayout = QHBoxLayout()
        buttonslayout.addWidget(btn_create)
        buttonslayout.addWidget(btn_edit)
        buttonslayout.addWidget(btn_view)
        buttonslayout.addWidget(btn_refresh)
        buttonslayout.addStretch()

        layoutmain = QVBoxLayout(self)
        layoutmain.addItem(buttonslayout)
        layoutmain.addWidget(self.tableviewclients)
        self.setLayout(layoutmain)

        self.agent_caroline = agent_caroline
        msg = {'type_message': 'find', 'type': 'caroline/client'}
        answer = self.agent_caroline.send_msg(msg)
        self.clients = answer['result']
        from sorter import Sorter
        sorter = Sorter()
        sorter.columns.add('name', 1)
        sorter.sort(self.clients)
        self.tablemodelclients.datasource = self.clients

        btn_create.clicked.connect(self.handle_btn_create_clicked)
        btn_refresh.clicked.connect(self.handle_btn_refresh_clicked)
        self.tableviewclients.handler_view = self.handle_table_view_clients_view
        self.tableviewclients.handler_edit = self.handle_table_view_clients_edit
        self.tableviewclients.handler_grant_credit = self.handle_table_view_clients_grant_credit

    def handle_btn_create_clicked(self):
        create_from = Dialog_Create_From(self)
        create_from.exec_()
        if create_from.create_from is not None:
            if create_from.create_from == 'reina/person':
                searcher = Search_Person(self)
            elif create_from.create_from == 'reina/corporation':
                searcher = Search_Corporation(self)
            else:
                searcher = None
            if searcher is not None:
                searcher.exec_()
                if searcher.selected is not None:
                    msg = {'type_message': 'find_one', 'type': 'caroline/client',
                           'query': {'id': searcher.selected['id']}}
                    answer = self.agent_caroline(msg)
                    if answer['result'] is not None:
                        QMessageBox.warning(self, 'Duplicated', 'ya se encuentra un cliente en la base de datos con el '
                                                                'mismo id.')
                    else:
                        client = searcher.selected
                        if QMessageBox.question(self, 'wholesale?', 'client has price wholesale?',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
                            client['wholesale'] = True
                        msg = {'type_message': 'action', 'action': 'caroline/create_client',
                               'client': client}
                        answer = self.agent_caroline(msg)
                        if 'error' in answer or 'client' not in answer:
                            QMessageBox.warning(self, 'error', 'an error has happened')
                        else:
                            QMessageBox.information(self, 'success', 'client has been created successfully')
                            self.tablemodelclients.insert_client(client=answer['client'])

    def handle_btn_refresh_clicked(self):
        msg = {'type_message': 'find', 'type': 'caroline/client'}
        answer = self.agent_caroline(msg)
        self.clients = answer['result']
        self.tablemodelclients.datasource = self.clients

    def handle_table_view_clients_view(self, i):
        viewer = Viewer_Client(self)
        viewer.client = self.clients[i]
        viewer.show()

    def handle_table_view_clients_edit(self, i):
        editor = Editor_Client(self)
        editor.client = self.clients[i]
        self.clients[i] = editor.client
        self.tablemodelclients.client_updated(i)
        editor.exec_()

    def handle_table_view_clients_grant_credit(self, i):
        client = self.clients[i]
        if 'account' in client:
            QMessageBox.information(self, 'ya tiene con credito', 'el cliente ya tiene una cuenta de credito')
        else:
            granter = Granter_Credit(self)
            granter.agent_caroline = self.agent_caroline
            granter.client = client
            granter.exec_()
            self.tablemodelclients.client_updated(i)


class Clients(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 500)
        self.setWindowTitle('Clients')
        self.agent_caroline = Client('isis.caroline.clients', 'caroline')
        self.cwidget = Central_Widget(self, agent_caroline=self.agent_caroline)
        self.setCentralWidget(self.cwidget)

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Clients()
    vv.show()
    sys.exit(app.exec_())
