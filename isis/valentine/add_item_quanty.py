from isis.dialog import Dialog
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.decimal_edit import Decimal_Edit
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout
from PySide2.QtWidgets import QSpacerItem, QSizePolicy
from isis.h_box_layout import H_Box_Layout
from isis.event import Event
from isis.itzamara.search_item import Search_Item
from utils import find_one
from isis.valentine.filter_after_searching import filter_after_searching
from PySide2.QtCore import QEvent, Qt


class Add_Item_Quanty(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 150)
        self.setWindowTitle('Agregar Articulo Cantidad')
        self.close_with_escape = True
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        lbl_quanty = Label('quanty: ', self)
        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()
        lbl_quanty.fix_size_based_on_font()

        self.lbl_sku = Label(self)
        self.txt_description = Line_Edit(self)
        self.dec_quanty = Decimal_Edit(self)

        self.dec_quanty.minimum = -1000
        self.dec_quanty.maximum = 1000
        self.dec_quanty.setDecimals(3)

        btn_accept = Push_Button('Aceptar', self)
        btn_close = Push_Button('Cerrar', self)

        layout_main = Grid_Layout(self)
        layout_main.addWidget(lbl_sku, 0, 0)
        layout_main.addWidget(self.lbl_sku, 0, 1)
        layout_main.addWidget(lbl_description, 1, 0)
        layout_main.addWidget(self.txt_description, 1, 1, 1, 4)
        layout_main.addWidget(lbl_quanty, 2, 0)
        layout_main.addWidget(self.dec_quanty, 2, 1)
        layout_main.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 3, 0, 1, -1)
        layout_buttons = H_Box_Layout()
        layout_buttons.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        layout_buttons.addWidget(btn_accept)
        layout_buttons.addWidget(btn_close)
        layout_main.addLayout(layout_buttons, 4, 0, 1, -1)
        self.layout = layout_main
        self._item = None

        self.add_item_quanty = Event()
        btn_accept.clicked.connect(self.accept)
        btn_close.clicked.connect(self.close)
        self.txt_description.installEventFilter(self)
        self.dec_quanty.installEventFilter(self)
        self.itemsrepository = None

    def search_item(self):
        searcher = Search_Item(self)
        if self.itemsrepository is not None:
            searcher.after_searching = filter_after_searching(self.itemsrepository)
        r = searcher.search(self.txt_description.text)
        if r is not None:
            if self.itemsrepository is not None:
                i = find_one(lambda x: x.sku == r.sku, self.itemsrepository)
            else:
                i = find_one(lambda x: x.sku == r.sku, cg.items_related)
            if i is not None:
                self.item = i
                self.dec_quanty.focus()
                self.dec_quanty.selectAll()
            else:
                self.item = None
        else:
            self.item = None

    def eventFilter(self, obj, event):
        if obj == self.dec_quanty and event.type() == QEvent.KeyPress and event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            if self.item is not None and self.dec_quanty.value is not None and self.dec_quanty.value != 0:
                self.accept()
            return True
        elif obj == self.txt_description and event.type() == QEvent.KeyPress and event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            if self.txt_description.text:
                self.search_item()
            return True
        else:
            return False

    def accept(self):
        if self.item is not None and self.dec_quanty.value is not None and self.dec_quanty.value != 0:
            self.add_item_quanty(self.item, self.dec_quanty.value)
            self.item = None
            self.dec_quanty.value = None
            self.txt_description.focus()

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item
        if item is not None:
            self.lbl_sku.text = item.sku if 'sku' in item else None
            self.txt_description.text = item.description if 'description' in item else None
        else:
            self.lbl_sku.text = None
            self.txt_description.text = None
