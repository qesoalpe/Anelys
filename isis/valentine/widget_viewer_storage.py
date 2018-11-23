from isis.label import Label
from isis.valentine.search_storage import Search_Storage
from isis.event import Event
from isis.push_button import Push_Button
from isis.grid_layout import Grid_Layout
from isis.group_box import Group_Box


class Widget_Viewer_Storage(Group_Box):
    def __init__(self, parent):
        Group_Box.__init__(self, parent)
        self.lbl_storage = Label('Storage', self)
        lbl_id = Label('id: ', self)
        lbl_name = Label('name: ', self)
        lbl_address = Label('address: ', self)

        self.lbl_id = Label(self)
        self.lbl_name = Label(self)
        self.lbl_address = Label(self)
        self.lbl_address.setWordWrap(True)
        lbl_id.fix_size_based_on_font()
        lbl_name.fix_size_based_on_font()
        lbl_address.fix_size_based_on_font()
        layout_main = Grid_Layout()
        layout_main.addWidget(self.lbl_storage, 0, 0)
        layout_main.addWidget(lbl_id, 1, 0)
        layout_main.addWidget(self.lbl_id, 1, 1)
        layout_main.addWidget(lbl_name, 1, 2)
        layout_main.addWidget(self.lbl_name, 1, 3)
        layout_main.addWidget(lbl_address, 2, 0)
        layout_main.addWidget(self.lbl_address, 2, 1, 1, -1)
        self.setLayout(layout_main)
        self._storage = None
        self._button_change = None
        self._with_button_change = False
        self.storage_changed = Event()

    @property
    def label(self):
        if self.lbl_storage is not None:
            return self.lbl_storage.text

    @label.setter
    def label(self, value):
        if value is None:
            self.lbl_storage.text = 'Storage'
        else:
            self.lbl_storage.text = value

    @property
    def with_button_change(self):
        return self._with_button_change

    @with_button_change.setter
    def with_button_change(self, value):
        from PySide2.QtCore import Qt
        if value and not self._with_button_change:
            self._button_change = Push_Button('change', self)
            self._button_change.clicked.connect(self.handle_btn_change_clicked)
            layout = self.layout()
            layout.addWidget(self._button_change, 0, 3, Qt.AlignRight)
        elif not value and self._with_button_change:
            layout = self.layout()
            layout.removeWidget(self._button_change)
            del self._button_change
        self._with_button_change = value

    def handle_btn_change_clicked(self):
        searcher = Search_Storage(self)
        searcher.exec_()
        if searcher.selected is not None:
            self.storage = searcher.selected

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage
        if storage is not None:
            self.lbl_id.setText(storage['id'] if 'id' in storage else None)
            self.lbl_name.setText(storage['name'] if 'name' in storage else None)
            self.lbl_address.setText(storage['address'] if 'address' in storage else None)
        else:
            self.lbl_id.text = None
            self.lbl_name.text = None
            self.lbl_address.text = None
        self.storage_changed(storage)
