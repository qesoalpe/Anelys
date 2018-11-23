from isis.grid_layout import Grid_Layout
from isis.push_button import Push_Button
from isis.group_box import Group_Box
from isis.label import Label
from isis.event import Event
from isis.piper.search_provider import Search_Provider
from PySide2.QtCore import Qt


class Widget_Viewer_Provider(Group_Box):
    def __init__(self, *args, **kwargs):
        Group_Box.__init__(self, *args, **kwargs)
        self._provider = None
        self.lbl_provider = Label('Provider', self)
        lbl_id = Label('id: ', self)
        lbl_name = Label('name: ', self)
        lbl_rfc = Label('rfc: ', self)
        self.lbl_id = Label(self)
        self.lbl_name = Label(self)
        self.lbl_rfc = Label(self)

        self.lbl_provider.fix_size_based_on_font()
        lbl_id.fix_size_based_on_font()
        lbl_name.fix_size_based_on_font()
        lbl_rfc.fix_size_based_on_font()

        self.buttons_layout = Grid_Layout()

        layoutmain = Grid_Layout(self)
        layoutmain.addWidget(self.lbl_provider, 0, 0)
        layoutmain.addLayout(self.buttons_layout, 0, 1, 1, -1, Qt.AlignRight)
        layoutmain.addWidget(lbl_id, 1, 0)
        layoutmain.addWidget(self.lbl_id, 1, 1)
        layoutmain.addWidget(lbl_rfc, 1, 2)
        layoutmain.addWidget(self.lbl_rfc, 1, 3)
        layoutmain.addWidget(lbl_name, 2, 0)
        layoutmain.addWidget(self.lbl_name, 2, 1, 1, -1)

        self.setLayout(layoutmain)
        self.provider_changed = Event()
        self._button_change = None
        self._button_quit = None

    @property
    def with_button_change(self):
        return self._button_change is not None

    @with_button_change.setter
    def with_button_change(self, value):
        if value and not self.with_button_change:
            self._button_change = Push_Button('Change', self)

            def handler():
                searcher = Search_Provider(self)
                searcher.exec_()
                result = searcher.selected
                if result is not None:
                    self.provider = result

            self._button_change.clicked.connect(handler)
            layout = self.buttons_layout
            layout.addWidget(self._button_change, 0, 2)
        else:
            layout = self.buttons_layout
            layout.removeWidget(self._button_change)
            del self._button_change

    @property
    def with_button_quit(self):
        return self._button_quit is not None

    @with_button_quit.setter
    def with_button_quit(self, value):
        layout = self.buttons_layout
        if value and not self.with_button_quit:
            self._button_quit = Push_Button('Quit', self)
            def ff():
                self.provider = None
            self._button_quit.clicked.connect(ff)
            layout.addWidget(self._button_quit, 0, 1)
        else:
            layout.removeWidget(self._button_quit)
            del self._button_quit

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, provider):
        self._provider = provider
        if provider is not None:
            for k in list(provider.keys()):
                if k not in ['id', 'name', 'business_name', 'rfc', 'address', 'type']:
                    del provider[k]
                    
            self.lbl_id.text = provider['id'] if 'id' in provider else None
            if 'name' in provider:
                self.lbl_name.setText(provider['name'])
            elif 'business_name' in provider:
                self.lbl_name.setText(provider['business_name'])
            else:
                self.lbl_name.text = None
            self.lbl_rfc.text = provider['rfc'] if 'rfc' in provider else None
        else:
            self.lbl_id.text = None
            self.lbl_name.text = None
            self.lbl_rfc.text = None
        self.provider_changed(provider)

    @property
    def label(self):
        return self.lbl_provider.text

    @label.setter
    def label(self, value):
        if value is not None:
            self.lbl_provider.text = value
        else:
            self.lbl_provider.text = 'Provider'
