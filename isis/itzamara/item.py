from PySide.QtCore import *
from PySide.QtGui import *


class Item(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        lbl_sku = QLabel('sku: ', self)
        btn_search_item = QPushButton('search_item', self)
        lbl_description = QLabel('description: ', self)
        lbl_unit = QLabel('unit: ', self)

        self.lbl_sku = QLabel(self)

        self.txt_description = QLineEdit(self)
        self.txt_unit = QLineEdit(self)

        mainlayout = QGridLayout(self)
        mainlayout.addWidget(lbl_sku, 0, 0)
        mainlayout.addWidget(self.lbl_sku, 0, 1)
        mainlayout.addWidget(btn_search_item, 0, 3, Qt.AlignRight)
        mainlayout.addWidget(lbl_description, 1, 0)
        mainlayout.addWidget(self.txt_description, 1, 1, 1, -1)
        mainlayout.addWidget(lbl_unit, 2, 0)
        mainlayout.addWidget(self.txt_unit, 2, 1)
        self.setLayout(mainlayout)
        self._item = None

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, x):
        self._item = x
        item = x
        if item is not None:
            if 'sku' in item:
                self.lbl_sku.setText(item['sku'])
            else:
                self.lbl_sku.setText('')
            if 'description' in item:
                self.txt_description.setText(item['description'])
            else:
                self.txt_description.setText('')
            if 'unit' in item:
                self.txt_unit.setText(item['unit'])
            else:
                self.txt_unit.setText('')
        else:
            self.lbl_sku.setText('')
            self.txt_description.setText('')
            self.txt_unit.setText('')


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Item()
    vv.show()
    vv.item = {'sku': '1020', 'description': 'BT(10) Maseca 1kg', 'unit': 'BT'}
    sys.exit(app.exec_())
