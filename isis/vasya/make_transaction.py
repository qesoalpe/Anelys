from isis.dialog import Dialog
from isis.label import Label
from PySide.QtGui import QGridLayout, QVBoxLayout
from isis.radio_group import Radio_Group


class Make_Transaction(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Make_Transaction')
        self.resize(500, 200)
        lbl_origen_id = Label('id: ', self)
        lbl_origen_name = Label('name: ', self)

        lbl_origen_id.fix_size_based_on_font()
        lbl_origen_name.fix_size_based_on_font()

        self.lbl_origen_id = Label(self)
        self.lbl_origen_name = Label(self)

        self.origen_direction = Radio_Group(self)
        self.origen_direction.items.add('ingress', 'in')
        self.origen_direction.items.add('egress', 'out')

        layoutmain = QVBoxLayout(self)
        layoutmain.addWidget(self.origen_direction)

        layoutorigen = QGridLayout()
        layoutorigen.addWidget(lbl_origen_id, 0, 0)
        layoutorigen.addWidget(self.lbl_origen_id, 0, 1)
        layoutorigen.addWidget(lbl_origen_name, 1, 0)
        layoutorigen.addWidget(self.lbl_origen_name, 1, 1)

        layoutmain.addLayout(layoutorigen)
        layoutmain.addStretch()

        self.setLayout(layoutmain)
        self._origen = None

    @property
    def origen(self):
        return self._origen

    @origen.setter
    def origen(self, origen):
        self._origen = origen
        if origen is not None:
            self.lbl_origen_id.text = origen['id'] if 'id' in origen else None
            self.lbl_origen_name.text = origen['name'] if 'name' in origen else None
        else:
            self.lbl_origen_id.text = None
            self.lbl_origen_name.text = None
