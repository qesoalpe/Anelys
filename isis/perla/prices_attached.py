from PySide.QtCore import *
from PySide.QtGui import *
from babel.numbers import format_currency
from sarah.acp_bson import Client
COLUMN_ID = 0
COLUMN_DESCRIPTION = 1
COLUMN_VALUE = 2
COLUMN_CONDITIONS = 3

class Table_Model(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self.rows = list()
    def rowCount(self, parent):
        return len(self.rows)

    def columnCount(self, parent):
        return 4

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            column = section
            if column == COLUMN_ID:
                return 'id'
            elif column == COLUMN_DESCRIPTION:
                return 'description'
            elif column == COLUMN_VALUE:
                return 'value'
            elif column == COLUMN_CONDITIONS:
                return 'conditions'

    def data(self, index, role):
        if role == Qt.DisplayRole:
            column = index.column()
            row = self.rows[index.row()]
            if column == COLUMN_ID:
                if 'id' in row:
                    return row['id']
            elif column == COLUMN_DESCRIPTION:
                if 'description' in row:
                    return row['description']
            elif column == COLUMN_VALUE:
                if 'value' in row:
                    return format_currency(row['value'], 'MXN', locale='es_mx')
            elif column == COLUMN_CONDITIONS:
                if 'conditions' in row:
                    if isinstance(row['conditions'], bool):
                        if row['conditions']:
                            return 'wholesale'
                        else:
                            return 'public'

    def flags(self, index):
        return Qt.ItemIsEnabled

    def set_prices(self, prices):
        self.rows = prices
        self.modelReset.emit()

    def clear_rows(self):
        i = len(self.rows) -1
        self.beginRemoveRows(QModelIndex(), 0, i if i >= 0 else 0)
        self.endRemoveRows()



class Table_View(QTableView):
    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.setModel(Table_Model())

class Prices_Attached(QDialog):
    def __init__(self, parent=None, product=None, agent_perla=None):
        QDialog.__init__(self, parent)
        self.agent_perla = agent_perla
        self.product = product
        self.setWindowTitle('prices attached')

        self.resize(600, 400)
        font = QFont()
        font.setFamily('arial')
        font.setPointSize(12)
        self.setFont(font)
        self.mainlayout = QVBoxLayout(self)

        self.productlayout = QGridLayout()
        self.lbl_product_header = QLabel('Product', self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(15)
        self.lbl_product_header.setFont(font)
        self.lbl_product_sku = QLabel(self)
        # self.lbl_product_sku.setFixedWidth(50)
        self.lbl_product_description = QLabel(self)
        # self.lbl_product_description.setFixedWidth(50)
        self.productlayout.addWidget(self.lbl_product_header, 0, 0, 1, 2)
        lbl_sku = QLabel('sku', self)
        lbl_sku.setFixedWidth(80)
        self.productlayout.addWidget(lbl_sku, 1, 0)
        lbl_description = QLabel('description', self)
        lbl_description.setFixedWidth(80)
        self.productlayout.addWidget(lbl_description, 2, 0)
        self.productlayout.addWidget(self.lbl_product_sku, 1, 1, 1, 1, Qt.AlignLeft)
        self.productlayout.addWidget(self.lbl_product_description, 2, 1, 1, Qt.AlignLeft)

        self.mainlayout.addItem(self.productlayout)


        self.tablelayout = QHBoxLayout()
        self.tableview = Table_View(self)
        self.tablemodel = self.tableview.model()
        self.tablelayout.addWidget(self.tableview)
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.btn_switch = QPushButton('switch', self)
        self.btn_add = QPushButton('+', self)
        self.btn_add.setFont(font)
        self.btn_remove = QPushButton('-', self)
        self.btn_remove.setFont(font)
        self.tablebuttonslayout = QVBoxLayout()
        self.tablebuttonslayout.addWidget(self.btn_switch)
        self.tablebuttonslayout.addWidget(self.btn_add)
        self.tablebuttonslayout.addWidget(self.btn_remove)
        self.tablebuttonslayout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.tablelayout.addItem(self.tablebuttonslayout)
        self.mainlayout.addItem(self.tablelayout)
        self.buttonslayout = QHBoxLayout()


        self.mainlayout.addItem(QSpacerItem(50, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.mainlayout.addItem(self.buttonslayout)
        self.buttonslayout.addItem(QSpacerItem(0, 50, QSizePolicy.Expanding))
        self.btn_accept = QPushButton('Aceptar', self)
        self.btn_cancel = QPushButton('Cancelar', self)
        self.buttonslayout.addWidget(self.btn_accept)
        self.buttonslayout.addWidget(self.btn_cancel)

        self.btn_accept.setDefault(True)
        self.accepted.connect(self.btn_accept.click)
        if self.product is not None:
            self.load_product(self.product)

    def load_product(self, product):
        self.product = product
        if 'sku' in product:
            self.lbl_product_sku.setText(product['sku'])
        else:
            self.lbl_product_header.setText('')
        if 'description' in product:
            self.lbl_product_description.setText(product['description'])
        else:
            self.lbl_product_description.setText('')
        if self.agent_perla is None:
            agent_perla = Client('isis.prices_attached', 'perla')
        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'perla/prices_attached', 'product': product}
        answer = agent_perla.send_msg(msg)
        if 'price' in answer:
            self.tablemodel.set_prices([answer['price']])
        elif 'prices' in answer:
            self.tablemodel.set_prices(answer['prices'])
        else:
            self.tablemodel.clear_rows()
        self.tableview.resizeColumnsToContents()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    vv = Prices_Attached(product={'sku': '1020', 'description': 'BT(10) Maseca 1kg'})
    vv.show()
    sys.exit(app.exec_())
