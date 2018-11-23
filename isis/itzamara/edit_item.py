from isis.itzamara.create_item import Create_Item
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.dialog import Dialog
from isis.v_box_layout import V_Box_Layout
from isis.h_box_layout import H_Box_Layout
from isis.combo_box import Combo_Box


class Edit_Item(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.window_title = 'itzamara/edit_item'

        lbl_sku = Label('sku: ', self)
        self.txt_sku = Line_Edit()

        lbl_description = Label('description: ', self)
        self.txt_descriptipn = Line_Edit(self)

        lbl_mass = Label('mass: ', self)
        self.txt_mass_n = Line_Edit(self)
        self.cmb_mass_unit = Combo_Box(self)

        self.cmb_mass_unit.addItems(['g', 'kg'])

        lbl_sku.fix_size_based_on_font()
        lbl_description.fix_size_based_on_font()

        layout_main = V_Box_Layout(self)
        layout = H_Box_Layout()
        layout.addWidget(lbl_sku)
        layout.addWidget(self.txt_sku)


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    d = Create_Item()
    d.show()
    sys.exit(app.exec_())
