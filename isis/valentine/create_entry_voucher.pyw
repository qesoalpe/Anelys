from isis.grid_layout import Grid_Layout
from isis.v_box_layout import V_Box_Layout
from isis.push_button import Push_Button
from isis.main_window import Main_Window
from isis.data_model.table import Table
from decimal import Decimal as D
from sarah.acp_bson import Client
from itzamara.remote import find_one_item
from isis.table_view import Table_View
from isis.widget import Widget
from isis.line_edit import Line_Edit
from isis.line_edit_command import Line_Edit_Command
from isis.dialog import Dialog
from isis.label import Label
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout
from isis.h_box_layout import H_Box_Layout
from isis.decimal_edit import Decimal_Edit
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QSpacerItem, QSizePolicy
from copy import deepcopy
from dict import Dict as dict, List as list
from datetime import datetime
from isodate import datetime_isoformat
from isis.itzamara.search_item import Search_Item
from isis.utils import parse_number


font = QFont()
font.setPointSize(15)


def current_datetime():
    return datetime_isoformat(datetime.now())


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns['sku'].changing_item_value = self.changing_item_value_sku
        self.columns['description'].changing_item_value = self.changing_item_value_description
        self.datasource = list()
        self.log = list()
        self.readonly = True

    def changing_item_value_sku(self, item, value):
        if value is not None and value:
            if 'sku' in item and value == item.sku:
                return False
            result = find_one_item(sku=value)
            if result is not None:
                self.set_item(item, result)
            else:
                self.clear_item(item)
        elif 'sku' in item:
            self.clear_item(item)
        else:
            return False

    def changing_item_value_description(self, item, value):
        if value is not None and value:
            if 'description' in item and value == item.description:
                return False
            from isis.itzamara.search_item import Search_Item
            searcher = Search_Item()
            result = searcher.search(value)
            if result is not None:
                self.set_item(item, result)
            else:
                self.clear_item(item)
        elif 'description' in item:
            self.clear_item(item)
        else:
            return False

    @staticmethod
    def set_item(item, new_item):
        if 'sku' in new_item:
            item.sku = new_item.sku
        elif 'sku' in item:
            del item.sku

        if 'description' in new_item:
            item.description = new_item.description
        elif 'description' in item:
            del item.description

        if 'type' in new_item:
            item.type = new_item.type
        elif 'type' in item:
            del item.type

    @staticmethod
    def clear_item(item):
        for k in list(item.keys()):
            if k in ['sku', 'description', 'type']:
                del item[k]

    def add_item(self, item):
        for old_item in self.datasource:
            if item.sku == old_item.sku:
                old_item.quanty += item.quanty
                log_item = dict({'item': deepcopy(item), 'quanty': item.quanty, 'action': 'sum',
                                 'datetime': current_datetime()})
                for k in list(log_item.item.keys()):
                    if k not in ['sku', 'type', 'description']:
                        del log_item.item[k]
                self.log.append(log_item)

                i = self.datasource.index(old_item)
                self.notify_row_changed(i)
                return i
        else:
            self.add_row(item)
            log_item = dict({'item': deepcopy(item), 'quanty': item.quanty, 'action': 'add',
                             'datetime': current_datetime()})
            for k in list(log_item.item.keys()):
                if k not in ['sku', 'description', 'type']:
                    del log_item.item[k]
            self.log.append(log_item)
            i = self.datasource.index(item)
            return i


class Question_Item_Quanty(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        # self.setFont(font)
        self.resize(400, 150)
        self.setWindowTitle('Cantidad')
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        lbl_quanty = Label('quanty: ', self)
        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()
        lbl_quanty.fix_size_based_on_font()

        self.lbl_sku = Label(self)
        self.lbl_description = Label(self)

        self.txt_quanty = Line_Edit(self)
        button_accept = Push_Button('Aceptar', self)
        button_close = Push_Button('Cerrar', self)
        self._item = None

        layoutmain = Grid_Layout(self)
        layoutmain.addWidget(lbl_sku, 0, 0)
        layoutmain.addWidget(self.lbl_sku, 0, 1)
        layoutmain.addWidget(lbl_description, 1, 0)
        layoutmain.addWidget(self.lbl_description, 1, 1, 1, 3)
        layoutmain.addWidget(lbl_quanty, 2, 0)
        layoutmain.addWidget(self.txt_quanty, 2, 1)
        layoutmain.addItem(QSpacerItem(50, 100), 3, 1, 1, -1)
        layoutbutton = H_Box_Layout()
        layoutbutton.addWidget(button_accept)
        layoutbutton.addWidget(button_close)
        layoutmain.addItem(layoutbutton, 4, 1, 1, -1)
        self.quanty = None

        button_accept.clicked.connect(self.accept)
        button_close.clicked.connect(self.close)
        self.close_with_escape = True

    def accept(self):
        from isis.utils import parse_number
        try:
            self.quanty = parse_number(self.txt_quanty.text)
        except:
            self.quanty = None
        self.close()

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item
        if item is not None:
            if 'sku' in item:
                self.lbl_sku.text = item.sku
            else:
                self.lbl_sku.text = None
            if 'description' in item:
                self.lbl_description.text = item.description
            else:
                self.lbl_description.text = None
        else:
            self.lbl_sku.text = None
            self.lbl_descriptione.text = None


class Question_Item_Expiration(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        # self.setFont(font)
        self.resize(400, 150)
        self.setWindowTitle('Caducidad')
        lbl_sku = Label('sku: ', self)
        lbl_description = Label('description: ', self)
        lbl_expiration = Label('expiration: ', self)
        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()
        lbl_expiration.fix_size_based_on_font()

        self.lbl_sku = Label(self)
        self.lbl_description = Label(self)

        self.txt_expiration = Line_Edit(self)
        button_accept = Push_Button('Aceptar', self)
        button_close = Push_Button('Cerrar', self)
        self._item = None

        layoutmain = Grid_Layout(self)
        layoutmain.addWidget(lbl_sku, 0, 0)
        layoutmain.addWidget(self.lbl_sku, 0, 1)
        layoutmain.addWidget(lbl_description, 1, 0)
        layoutmain.addWidget(self.lbl_description, 1, 1, 1, 3)
        layoutmain.addWidget(lbl_expiration, 2, 0)
        layoutmain.addWidget(self.txt_expiration, 2, 1)
        layoutmain.addItem(QSpacerItem(50, 100), 3, 1, 1, -1)
        layoutbutton = H_Box_Layout()
        layoutbutton.addWidget(button_accept)
        layoutbutton.addWidget(button_close)
        layoutmain.addItem(layoutbutton, 4, 1, 1, -1)
        self.expiration = None

        button_accept.clicked.connect(self.accept)
        button_close.clicked.connect(self.close)
        self.close_with_escape = True

    def accept(self):
        try:
            self.expiration = self.txt_expiration.text
        except:
            self.expiration = None
        self.close()

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item
        if item is not None:
            if 'sku' in item:
                self.lbl_sku.text = item.sku
            else:
                self.lbl_sku.text = None
            if 'description' in item:
                self.lbl_description.text = item.description
            else:
                self.lbl_description.text = None
        else:
            self.lbl_sku.text = None
            self.lbl_descriptione.text = None


class Create_Entry_Voucher(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        # self.setFont(font)
        self.setWindowTitle('Crear Vale de Entrada')
        self.resize(400, 600)
        self.cwidget = Widget(self)

        self.tableview = Table_View(self.cwidget)
        self.itemsmodel = Items_Model()
        self.tableview.model = self.itemsmodel
        self.txt_command = Line_Edit_Command(self.cwidget)
        btn_add_item = Push_Button('Agregar Articulo', self.cwidget)

        layout_main = V_Box_Layout()
        layout_main.addWidget(self.tableview)
        layout_main.addWidget(self.txt_command)
        layout_main.addWidget(btn_add_item)
        self.cwidget.layout = layout_main

        self.txt_command.command.suscribe(self.command)
        self.log = list()
        self.itemsmodel.log = self.log

        btn_add_item.clicked.connect(self.handle_btn_add_item)

    def command(self, value):
        searcher = Search_Item(self)
        result = searcher.search(value)
        if result is not None:
            qq = Question_Item_Quanty(self)
            qq.item = result
            qq.exec_()
            quanty = qq.quanty
            if quanty is not None:
                item = result
                item.quanty = quanty
                self.tableview.selectRow(self.itemsmodel.add_item(item))

    def handle_btn_add_item(self):
        searcher = Search_Item(self)
        searcher.exec_()
        result = searcher.selected
        if result is not None:
            qq = Question_Item_Quanty(self)
            qq.item = result
            qq.exec_()
            quanty = qq.quanty
            if quanty is not None:
                item = result
                item.quanty = quanty
                self.tableview.selectRow(self.itemsmodel.add_item(item))


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Create_Entry_Voucher()
    mw.show()
    sys.exit(app.exec_())
