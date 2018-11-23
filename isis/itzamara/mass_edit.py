from katherine import d6
from isis.widget import Widget
from isis.line_edit import Line_Edit
from isis.combo_box import Combo_Box
from isis.h_box_layout import H_Box_Layout
from isis.utils import format_number
from utils import isnumeric
from dict import Dict as dict
from decimal import Decimal as D

try:
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('select symbol from itzamara.unit_mass;')
    units_mass = [s for s, in d6_cursor]
    d6_cursor.close()
except:
    units_mass = ['g', 'lb', 'kg']


class Mass_Edit(Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.txt_n = Line_Edit(self)
        self.cmb_unit = Combo_Box(self)
        self.cmb_unit.addItems(units_mass)

        self.layout = H_Box_Layout(self)
        self.layout.addWidget(self.txt_n)
        self.layout.addWidget(self.cmb_unit)

    @property
    def mass(self):
        if self.txt_n.text.strip() and isnumeric(self.txt_n.text.strip()):
            return dict({'n': D(self.txt_n.text.strip()), 'unit': self.cmb_unit.currentText()})

    @mass.setter
    def mass(self, mass):
        self.txt_n.text = format_number(mass.n)
        self.cmb_unit.setCurrentText(mass.unit)
