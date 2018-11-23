from isis.label import Label
from isis.caroline.search_client import Search_Client
from dict import Dict as dict
from isis.group_box import Group_Box
from isis.grid_layout import Grid_Layout
from isis.check_box import Check_Box
from PySide2.QtCore import Qt
from PySide2.QtGui import QKeyEvent


class Widget_Client(Group_Box):
    def __init__(self, *args, **kwargs):
        Group_Box.__init__(self, *args, **kwargs)
        lbl_client = Label('Client', self)
        self._lbl_id = Label('id: ', self)
        self._lbl_name = Label('name: ', self)
        self._lbl_wholesale = Label('wholesale: ', self)
        self._lbl_rfc = Label('rfc: ', self)
        self._lbl_address = Label('address : ', self)

        self._lbl_address.fix_size_based_on_font()
        self._lbl_name.fix_size_based_on_font()
        self._lbl_wholesale.fix_size_based_on_font()
        self._lbl_rfc.fix_size_based_on_font()
        self._lbl_address.fix_size_based_on_font()

        self.lbl_id = Label(self)
        self.lbl_name = Label(self)
        self.txt_name = None

        self.chk_wholesale = Check_Box(self)
        self.lbl_rfc = Label(self)
        self.lbl_address = Label(self)

        self._client = None

        layoutmain = Grid_Layout(self)
        layoutmain.addWidget(lbl_client, 0, 0)
        layoutmain.addWidget(self._lbl_id, 1, 0)
        layoutmain.addWidget(self.lbl_id, 1, 1)
        layoutmain.addWidget(self._lbl_name, 2, 0)
        layoutmain.addWidget(self.lbl_name, 2, 1, 1, -1)
        layoutmain.addWidget(self._lbl_wholesale, 3, 0)
        layoutmain.addWidget(self.chk_wholesale, 3, 1)
        layoutmain.addWidget(self._lbl_rfc, 3, 2)
        layoutmain.addWidget(self.lbl_rfc, 3, 3)
        layoutmain.addWidget(self._lbl_address, 4, 0)
        layoutmain.addWidget(self.lbl_address, 4, 1, 1, -1)

        self.setLayout(layoutmain)

        self.chk_wholesale.stateChanged.connect(self.handle_chk_wholesale_stateChanged)

    def handle_chk_wholesale_stateChanged(self, v):
        client = self.client
        if client is not None:
            if 'id' in client:
                self.chk_wholesale.setChecked(client.wholesale if 'wholesale' in client else False)
                return
            client.wholesale = self.chk_wholesale.isChecked()
        else:
            client = dict({'wholesale': self.chk_wholesale.isChecked()})
            self._client = client

    def handle_txt_name_text_edited(self, text):
        if self._client is None:
            self._client = dict({'name': text})
        else:
            self._client.name = text
        if self.with_wholesale and not self.chk_wholesale.isEnabled():
            self.chk_wholesale.setEnabled(True)

        for k in list(self._client.keys()):
            if k not in ['wholesale', 'name']:
                if k == 'id':
                    self.lbl_id.text = None
                elif k == 'rfc':
                    if self.with_rfc:
                        self.lbl_rfc.text = None
                elif k == 'address':
                    if self.with_address:
                        self.lbl_address.text = None
                del self._client[k]

    def handle_search_txt_name(self, text):
        searcher = Search_Client(self)
        result = searcher.search(text)
        if result is not None:
            self.client = result

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client
        if client is not None:
            self.lbl_id.text = client.id if 'id' in client else None

            if 'business_name' in client:
                name = client.business_name
            elif 'name' in client:
                name = client.name
            else:
                name = None

            if self.name_editable:
                self.txt_name.text = name
            else:
                self.lbl_name.text = name

            if self.with_wholesale:
                self.chk_wholesale.setChecked(client.wholesale if 'wholesale' in client else False)
                self.chk_wholesale.setEnabled('id' not in client)

            if self.with_rfc:
                self.lbl_rfc.text = client.rfc if 'rfc' in client else None

            if self.with_address:
                self.lbl_address.text = client.address if 'address' in client else None

        else:
            self.lbl_id.text = None
            if self.name_editable:
                self.txt_name.text = None
            else:
                self.lbl_name.text = None
            if self.with_wholesale:
                self.chk_wholesale.setEnabled(True)
                # self.chk_wholesale.setChecked(False)
            if self.with_rfc:
                self.lbl_rfc.text = None
            if self.with_address:
                self.lbl_address.text = None

    @property
    def name_editable(self):
        return self.lbl_name is None

    @name_editable.setter
    def name_editable(self, value):
        layout = self.layout()
        if value and not self.name_editable:
            from isis.line_edit import Line_Edit
            self.txt_name = Line_Edit(self)
            layout.removeWidget(self.lbl_name)
            del self.lbl_name
            self.lbl_name = None
            layout.addWidget(self.txt_name, 2, 1, 1, -1)
            self.txt_name.text_edited.suscribe(self.handle_txt_name_text_edited)
            def handler(event):
                if isinstance(event, QKeyEvent):
                    if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                        self.handle_search_txt_name(self.txt_name.text)
            self.txt_name.key_down.suscribe(handler)
        elif not value and self.name_editable:
            self.lbl_name = Label(self)
            layout.removeWidget(self.txt_name)
            del self.txt_name
            self.txt_name = None
            layout.addWidget(self.lbl_name, 2, 1, 1, -1)

    @property
    def with_wholesale(self):
        return self.chk_wholesale is not None

    @property
    def with_rfc(self):
        return self.lbl_rfc is not None

    @property
    def with_address(self):
        return self.lbl_address is not None
