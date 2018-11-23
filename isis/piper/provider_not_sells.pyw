from sarah.acp_bson import Client
from PySide.QtGui import QDialog, QTableView, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QSpacerItem
from PySide.QtCore import Qt, QAbstractTableModel, QModelIndex
from isis.piper.search_provider import Search_Provider
from isis.itzamara.search_item import Search_Item
COLUMN_SKU = 0
COLUMN_DESCRIPTION = 1


class Table_Model_Items(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.items = list()

    def columnCount(self, parent):
        return 2

    def rowCount(self, parent):
        return len(self.items)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == COLUMN_SKU:
                return 'sku'
            elif section == COLUMN_DESCRIPTION:
                return 'description'

    def insert_item(self, i=None, item=None):
        if i is None:
            i = len(self.items)
        if item is None:
            item = dict()
        self.beginInsertRows(QModelIndex(), i, i)
        self.items.insert(i, item)
        self.endInsertRows()

    def remove_item(self, i=None, item=None):
        if i is not None:
            self.beginRemoveRows(QModelIndex(), i, i)
            del self.items[i]
            self.endRemoveRows()
        elif item is not None:
            i = self.items.index(item)
            self.beginRemoveRows(QModelIndex(), i, i)
            del self.items[i]
            self.endRemoveRows()

    def clear(self):
        self.items.clear()
        self.modelReset.emit()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = self.items[index.row()]
            if index.column() == COLUMN_SKU:
                if 'sku' in row:
                    return row['sku']
            elif index.column() == COLUMN_DESCRIPTION:
                if 'description' in row:
                    return row['description']


class Table_View_Items(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)


class Provider_Not_Sells(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.resize(450, 600)
        self.setWindowTitle('Provider_Not_Sells')
        # layout provider start
        layoutprovider = QGridLayout()
        lbl_provider = QLabel('provider', self)
        lbl_provider_id = QLabel('id: ', self)
        lbl_provider_name = QLabel('name: ', self)
        lbl_provider_type = QLabel('type: ', self)
        self.lbl_provider_id = QLabel(self)
        self.lbl_provider_name = QLabel(self)
        self.lbl_provider_type = QLabel(self)
        self.btn_change_provider = QPushButton('change provider', self)
        lbl_provider_id.setFixedWidth(lbl_provider_id.fontMetrics().width(lbl_provider_id.text()))
        lbl_provider_name.setFixedWidth(lbl_provider_name.fontMetrics().width(lbl_provider_name.text()))
        lbl_provider_type.setFixedWidth(lbl_provider_type.fontMetrics().width(lbl_provider_type.text()))
        layoutprovider.addWidget(lbl_provider, 0, 0)
        layoutprovider.addWidget(self.btn_change_provider, 0, 1, Qt.AlignRight)
        layoutprovider.addWidget(lbl_provider_id, 1, 0)
        layoutprovider.addWidget(self.lbl_provider_id, 1, 1)
        layoutprovider.addWidget(lbl_provider_type, 2, 0)
        layoutprovider.addWidget(self.lbl_provider_type, 2, 1)
        layoutprovider.addWidget(lbl_provider_name, 3, 0)
        layoutprovider.addWidget(self.lbl_provider_name, 3, 1)
        # layoutprovider ends

        self.tablemodelitems = Table_Model_Items(self)
        self.tableviewitems = Table_View_Items(self)
        self.tableviewitems.setModel(self.tablemodelitems)
        self.btn_add_item = QPushButton('+', self)
        self.btn_remove_item = QPushButton('-', self)

        layouttableitems = QHBoxLayout()
        layouttableitems.addWidget(self.tableviewitems)
        layoutbuttonestable = QVBoxLayout()
        layoutbuttonestable.addWidget(self.btn_add_item)
        layoutbuttonestable.addWidget(self.btn_remove_item)
        layoutbuttonestable.addStretch()
        layouttableitems.addItem(layoutbuttonestable)

        mainlayout = QVBoxLayout(self)
        mainlayout.addItem(layoutprovider)
        mainlayout.addItem(layouttableitems)
        self.setLayout(mainlayout)

        self.provider = None
        self.agent_piper = Client(Provider_Not_Sells.APP_ID, 'piper')
        self.update_provider_ui()

        self.btn_change_provider.clicked.connect(self.handle_btn_change_provider_clicked)
        self.btn_add_item.clicked.connect(self.handle_btn_add_item_clicked)
        self.btn_remove_item.clicked.connect(self.handle_btn_remove_item_clicked)

    APP_ID = 'isis.piper.provider_not_sells'

    def handle_btn_change_provider_clicked(self):
        searcher = Search_Provider(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.provider = searcher.selected
            self.update_provider_ui()
            self.update_table_items()

    def handle_btn_add_item_clicked(self):
        if self.provider is not None and 'id' in self.provider:
            searcher = Search_Item(self)
            searcher.exec_()
            if searcher.selected is not None and 'sku' in searcher.selected:
                for item in self.tablemodelitems.items:
                    if item['sku'] == searcher.selected['sku']:
                        break
                else:
                    self.tablemodelitems.insert_item(item=searcher.selected)
                    self.tableviewitems.resizeColumnsToContents()
                    msg = {'type_message': 'action', 'action': 'piper/create_provider_not_sells',
                           'provider': self.provider, 'item': searcher.selected}
                    self.agent_piper.send_msg(msg)

    def handle_btn_remove_item_clicked(self):
        index = self.tableviewitems.currentIndex()
        if index.isValid():
            item = self.tablemodelitems.items[index.row()]
            self.tablemodelitems.remove_item(item=item)
            self.tableviewitems.resizeColumnsToContents()
            if self.provider is not None and 'id' in self.provider and item is not None and 'sku' in item:
                msg = {'type_message': 'action', 'action': 'piper/remove_provider_not_sells', 'provider': self.provider,
                       'item': item}
                self.agent_piper.send_msg(msg)


    def update_provider_ui(self):
        if self.provider is not None:
            if 'id' in self.provider:
                self.lbl_provider_id.setText(self.provider['id'])
            else:
                self.lbl_provider_id.setText('')
            if 'type' in self.provider:
                self.lbl_provider_type.setText(self.provider['type'])
            else:
                self.lbl_provider_type.setText('')
            if 'business_name' in self.provider:
                self.lbl_provider_name.setText(self.provider['business_name'])
            elif 'name' in self.provider:
                self.lbl_provider_name.setText(self.provider['name'])
            else:
                self.lbl_provider_name.setText('')
        else:
            self.lbl_provider_id.setText('')
            self.lbl_provider_type.setText('')
            self.lbl_provider_name.setText('')

    def update_table_items(self):
        self.tablemodelitems.clear()
        if self.provider is not None and 'id' in self.provider:
            msg = {'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_not_sells',
                   'provider': {'id': self.provider['id']}}
            answer = self.agent_piper.send_msg(msg)
            for item in answer['result']:
                if isinstance(item, dict):
                    self.tablemodelitems.insert_item(item=item)
                elif isinstance(item, str):
                    self.tablemodelitems.insert_item(item={'sku': item})
        self.tableviewitems.resizeColumnsToContents()


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Provider_Not_Sells()
    sys.exit(vv.exec_())
