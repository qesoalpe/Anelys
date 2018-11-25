from isis.group_box import Group_Box
from isis.label import Label
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout
from isis.h_box_layout import H_Box_Layout
from PySide2.QtCore import Qt
from isis.event import Event
from isis.valentine.search_supplier import Search_Supplier


class Widget_Viewer_Supplier(Group_Box):
    def __init__(self, *args, **kwargs):
        Group_Box.__init__(self, *args, **kwargs)
        lbl_id = Label('id: ', self)
        lbl_type = Label('type: ', self)
        lbl_name = Label('name: ', self)
        self.lbl_id = Label(self)
        self.lbl_type = Label(self)
        self.lbl_name = Label(self)
        lbl_id.fix_size_based_on_font()
        lbl_type.fix_size_based_on_font()
        lbl_name.fix_size_based_on_font()

        btn_remove = Push_Button('remove', self)
        btn_change = Push_Button('change', self)

        layout_main = Grid_Layout(self)
        layout_main.addWidget(lbl_id, 0, 0)
        layout_main.addWidget(self.lbl_id, 0, 1)
        layout_main.addWidget(lbl_type, 0, 2)
        layout_main.addWidget(self.lbl_type, 0, 3)
        buttons_layout = H_Box_Layout()
        buttons_layout.addWidget(btn_remove)
        buttons_layout.addWidget(btn_change)
        layout_main.addLayout(buttons_layout, 0, 4, Qt.AlignRight)
        layout_main.addWidget(lbl_name, 1, 0)
        layout_main.addWidget(self.lbl_name, 1, 1, 1, -1)
        self._supplier = None
        btn_change.clicked.connect(self.handle_btn_change)
        btn_remove.clicked.connect(self.handle_btn_remove)
        self.supplier_changed = Event()

    def handle_btn_change(self):
        searcher = Search_Supplier(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.supplier = searcher.selected

    def handle_btn_remove(self):
        self.supplier = None

    @property
    def supplier(self):
        return self._supplier

    @supplier.setter
    def supplier(self, supplier):
        self._supplier = supplier
        self.supplier_changed(supplier)
        if supplier is None:
            self.lbl_id.text = None
            self.lbl_type.text = None
            self.lbl_name.text = None

        else:
            self.lbl_id.text = supplier.id if 'id' in supplier else None

            for k in ['supplier_type', 'type']:
                if k in supplier:
                    self.lbl_type.text = supplier[k]
                    break
            else:
                self.lbl_type.text = None

            for k in ['business_name', 'name', 'rfc']:
                if k in supplier:
                    self.lbl_name.text = supplier[k]
                    break
            else:
                self.lbl_name.text = None
