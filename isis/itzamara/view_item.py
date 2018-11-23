from isis.dialog import Dialog
from isis.label import Label
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout


class Viewer_Item(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.resize(300, 200)
        self.window_title = 'itzamara/view_item'

        lbl_sku = Label('sku: ', self)
        self.lbl_sku = Label(self)
        lbl_description = Label('description: ', self)
        self.lbl_description = Label(self)
        self.btn_close = Push_Button('close', self)

        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()
        buttonslayout = QHBoxLayout()
        buttonslayout.addStretch()
        buttonslayout.addWidget(self.btn_close)

        mainlayout = QGridLayout(self)
        mainlayout.addWidget(lbl_sku, 0, 0)
        mainlayout.addWidget(self.lbl_sku, 0, 1)
        mainlayout.addWidget(lbl_description, 1, 0)
        mainlayout.addWidget(self.lbl_description, 1, 1)
        mainlayout.addItem(QSpacerItem(50, 50, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0, 1, -1)
        mainlayout.addItem(buttonslayout, 3, 0, 1, -1)
        self.setLayout(mainlayout)
        self._item = None

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, s):
        self._item = s
        self.update_item_ui()

    def update_item_ui(self):
        if self.item is not None:
            if 'sku' in self.item:
                self.lbl_sku.setText(self.item['sku'])
            else:
                self.lbl_sku.setText('')
            if 'description' in self.item:
                self.lbl_description.setText(self.item['description'])
            else:
                self.lbl_description.setText('')
        else:
            self.lbl_sku.setText('')
            self.lbl_description.setText('')


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Viewer_Item()
    vv.item = {'sku': '1020', 'description': 'BT(10) Maseca 1kg'}
    vv.show()
    sys.exit(app.exec_())
