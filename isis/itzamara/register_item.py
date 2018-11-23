from PySide.QtGui import *
from PySide.QtCore import *
from isis.label import Label
from isis.itzamara.search_item import Search_Item


class Register_Item(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Register_Item')
        self.resize(500, 100)
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        lbl_unit_measure = Label('unit_measure: ', self)
        self.lbl_sku = Label(self)
        self.txt_description = QLineEdit(self)
        self.txt_unit_measure = QLineEdit(self)
        self.chk_pack = QCheckBox('pack', self)

        btn_save = QPushButton('save', self)
        btn_close = QPushButton('close', self)
        btn_new = QPushButton('new', self)
        btn_codes_ref = QPushButton('codes_ref', self)
        btn_manage_prices = QPushButton('manage_prices', self)
        layoutmain = QVBoxLayout(self)
        layout = QGridLayout()

        layout.addWidget(lbl_sku,  0, 0)
        layout.addWidget(self.lbl_sku, 0, 1)
        layout.addWidget(lbl_description, 1, 0)
        layout.addWidget(self.txt_description, 1, 1, 1, -1)
        layout.addWidget(lbl_unit_measure, 2, 0)
        layout.addWidget(self.txt_unit_measure, 2, 1)
        layout.addWidget(self.chk_pack, 2, 2)
        layout.addWidget(btn_new, 2, 3)
        layout.addWidget(btn_codes_ref, 2, 4)
        layout.addWidget(btn_manage_prices,2, 5)

        layoutmain.addLayout(layout)

        buttonslayout = QHBoxLayout()
        buttonslayout.addStretch()
        buttonslayout.addWidget(btn_save)
        buttonslayout.addWidget(btn_close)
        layoutmain.addLayout(buttonslayout)
        layoutmain.addStretch()
        self.setLayout(layoutmain)

        self.chk_pack.stateChanged.connect(self.handle_chk_pack_stateChanged)

    def handle_chk_pack_stateChanged(self, state):
        pass


if __name__ == '__main__':
    from PySide.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    d = Register_Item()
    d.show()
    sys.exit(app.exec_())
