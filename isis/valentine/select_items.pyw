from isis.dialog import Dialog
from isis.itzamara.search_item import Search_Item
from isis.table_view import Table_View
from isis.data_model.table import Table
from utils import find_one
from itzamara.remote import find_one_item
from PySide2.QtWidgets import QSpacerItem, QSizePolicy
from isis.v_box_layout import V_Box_Layout
from isis.push_button import Push_Button
from isis.h_box_layout import H_Box_Layout
from isis.valentine.filter_after_searching import filter_after_searching


class Items_Model(Table):
    def __init__(self, parentgui=None):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)

        self.itemsrepository = None
        self.with_new_empty_row = True
        self.readonly = True
        self.parentgui = parentgui
        self.creating_row.suscribe(self.handle_creating_row)

    def handle_creating_row(self, column, value):
        if column == self.columns['sku']:
            if self.itemsrepository is not None:
                return find_one(lambda x: x.sku == value, self.itemsrepository)
            else:
                return find_one_item(sku=value)
        elif column == self.columns['description']:
            searcher = Search_Item(self.parentgui)
            if self.itemsrepository is not None:
                searcher.after_searching = filter_after_searching(self.itemsrepository)
            item = searcher.search(value)
            if self.itemsrepository is not None and item is not None:
                item = find_one(lambda x: x.sku == item.sku, self.itemsrepository)
            return item


class Select_Items(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(450, 600)
        self.setWindowTitle('Seleccionar Items')

        self.table = Table_View(self)
        self.table.enable_delete_row_with_supr = True

        self.itemsmodel = Items_Model(parentgui=self)

        self.table.model = self.itemsmodel

        btn_accept = Push_Button('Aceptar', self)
        btn_close = Push_Button('Cerrar', self)

        layoutmain = V_Box_Layout(self)
        layoutmain.addWidget(self.table)
        layoutbutton = H_Box_Layout()
        layoutbutton.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding))
        layoutbutton.addWidget(btn_accept)
        layoutbutton.addWidget(btn_close)
        layoutmain.addLayout(layoutbutton)

        btn_accept.clicked.connect(self.accept)
        btn_close.clicked.connect(self.reject)

    def accept(self):
        self.done(Dialog.Accepted)

    @property
    def items(self):
        return self.itemsmodel.datasource

    @property
    def itemsrepository(self):
        return self.itemsmodel.itemsrepository

    @itemsrepository.setter
    def itemsrepository(self, ir):
        self.itemsmodel.itemsrepository = ir


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    d = Select_Items()
    d.show()
    sys.exit(app.exec_())
