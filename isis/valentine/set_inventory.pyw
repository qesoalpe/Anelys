from PySide2.QtCore import Qt
from isis.dialog import Dialog
from isis.push_button import Push_Button
from isis.h_box_layout import H_Box_Layout
from isis.v_box_layout import V_Box_Layout
from isis.grid_layout import Grid_Layout
from isis.line_edit import Line_Edit
from isis.label import Label
from isis.decimal_edit import Decimal_Edit
from isis.message_box import Message_Box
from isis.itzamara.search_item import Search_Item
from sarah.acp_bson import Client
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage


class Set_Inventory(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Set_Inventory')

        self.viewer_storage = Widget_Viewer_Storage(self)
        self.viewer_storage.with_button_change = True

        lbl_item = Label('item', self)
        btn_change_item = Push_Button('change_&item', self)
        lbl_item_sku = Label('sku: ', self)
        lbl_item_description = Label('description: ', self)

        self.lbl_item_sku = Label(self)
        self.lbl_item_description = Label(self)

        lbl_quanty = Label('quanty: ', self)
        self.spin_quanty = Decimal_Edit(self)

        btn_accept = Push_Button('accept', self)
        btn_close = Push_Button('&close', self)
        btn_accept.setDefault(True)

        lbl_item_sku.fix_size_based_on_font()
        lbl_item_description.fix_size_based_on_font()
        lbl_quanty.fix_size_based_on_font()

        mainlayout = Grid_Layout(self)
        mainlayout.addWidget(self.viewer_storage, 0, 0, 1, -1)
        mainlayout.addWidget(lbl_item, 1, 0)
        mainlayout.addWidget(btn_change_item, 1, 1, Qt.AlignRight)
        mainlayout.addWidget(lbl_item_sku, 2, 0)
        mainlayout.addWidget(self.lbl_item_sku, 2, 1)
        mainlayout.addWidget(lbl_item_description, 3, 0)
        mainlayout.addWidget(self.lbl_item_description, 3, 1)
        mainlayout.addWidget(lbl_quanty, 4, 0)
        mainlayout.addWidget(self.spin_quanty, 4, 1)

        layoutbuttons = H_Box_Layout()
        layoutbuttons.addStretch()
        layoutbuttons.addWidget(btn_accept)
        layoutbuttons.addWidget(btn_close)

        mainlayout.addItem(layoutbuttons)
        self.setLayout(mainlayout)

        self.storage = None
        self.item = None
        self.agent_valentine = None

        btn_change_item.clicked.connect(self.handle_btn_change_item_clicked)
        btn_close.clicked.connect(self.close)
        btn_accept.clicked.connect(self.handle_btn_accept_clicked)
        self.spin_quanty.setMaximum(10000)
        self.spin_quanty.setFocus()

    @property
    def storage(self):
        return self.viewer_storage.storage

    @storage.setter
    def storage(self, storage):
        self.viewer_storage.storage = storage

    def handle_btn_change_item_clicked(self):
        searcher = Search_Item(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.item = searcher.selected
            self.update_item_ui()
            self.spin_quanty.setFocus()

    def handle_btn_accept_clicked(self):
        if self.item is not None and self.storage is not None:
            if self.agent_valentine is None:
                self.agent_valentine = Client('isis.valentine.set_inventory', 'valentine')
            from decimal import Decimal
            msg = {'type_message': 'action', 'action': 'valentine/set_inventory', 'item': self.item,
                   'storage': self.storage}
            self.item['inventory'] = round(Decimal(self.spin_quanty.value), 3)
            self.agent_valentine.send_msg(msg)
            Message_Box.information(self, 'changed', 'invetory setted')
            self.item = None
            self.update_item_ui()
            self.spin_quanty.value = 0
            searcher = Search_Item(self)
            searcher.exec_()
            if searcher.selected is not None:
                self.item = searcher.selected
                self.update_item_ui()
                self.spin_quanty.setFocus()

    def update_storage_ui(self):
        if self.storage is not None:
            if 'id' in self.storage:
                self.lbl_storage_id.setText(self.storage['id'])
            else:
                self.lbl_storage_id.setText('')
            if 'name' in self.storage:
                self.lbl_storage_name.setText(self.storage['name'])
            else:
                self.lbl_storage_name.setText('')
        else:
            self.lbl_storage_id.setText('')
            self.lbl_storage_name.setText('')

    def update_item_ui(self):
        if self.item is not None:
            if 'sku' in self.item:
                self.lbl_item_sku.setText(self.item['sku'])
            else:
                self.lbl_item_sku.setText('')
            if 'description' in self.item:
                self.lbl_item_description.setText(self.item['description'])
            else:
                self.lbl_item_description.setText('')
        else:
            self.lbl_item_sku.setText('')
            self.lbl_item_description.setText('')


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Set_Inventory()
    vv.show()
    sys.exit(app.exec_())
