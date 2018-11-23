from isis.v_box_layout import V_Box_Layout
from isis.dialog import Dialog
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.push_button import Push_Button
from isis.message_box import Message_Box
from isis.h_box_layout import H_Box_Layout
from PySide2.QtWidgets import QSpacerItem
from isis.itzamara.code_ref import Code_Ref_Table_View, Code_Ref_Model
from dict import Dict as dict
from sarah.acp_bson import Client
from isis.event import Event
from isis.itzamara.mass_edit import Mass_Edit


agent_itzamara = Client('', 'itzamara')


class Create_Item(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(500, 300)
        self.window_title = 'itzamara/create_item'

        lbl_description = Label('description: ', self)
        self.txt_description = Line_Edit(self)

        lbl_unit_measure = Label('unit measure: ', self)
        self.txt_unit_measure = Line_Edit(self)

        lbl_lifetime = Label('lifetime: ', self)
        self.txt_lifetime = Line_Edit(self)

        lbl_mass = Label('mass: ', self)
        self.mass_edit = Mass_Edit(self)

        lbl_description.fix_size_based_on_font()
        lbl_unit_measure.fix_size_based_on_font()
        lbl_lifetime.fix_size_based_on_font()
        lbl_mass.fix_size_based_on_font()

        self.code_ref_model = Code_Ref_Model(parent_gui=self)
        self.table = Code_Ref_Table_View(self)
        self.table.model = self.code_ref_model

        btn_create = Push_Button('create', self)
        btn_close = Push_Button('close', self)

        layout_main = V_Box_Layout(self)
        layout_description = H_Box_Layout()
        layout_description.addWidget(lbl_description)
        layout_description.addWidget(self.txt_description)
        layout_main.addLayout(layout_description)
        layout_unit_measure = H_Box_Layout()
        layout_unit_measure.addWidget(lbl_unit_measure)
        layout_unit_measure.addWidget(self.txt_unit_measure)
        layout_unit_measure.addWidget(lbl_lifetime)
        layout_unit_measure.addWidget(self.txt_lifetime)
        layout_main.addLayout(layout_unit_measure)
        layout_mass = H_Box_Layout()
        layout_mass.addWidget(lbl_mass)
        layout_mass.addWidget(self.txt_mass_n)
        layout_mass.addWidget(self.cmb_mass_unit)
        layout_mass.addStretch()
        layout_main.addLayout(layout_mass)
        layout_main.addWidget(self.table)
        buttons_layout = H_Box_Layout()
        buttons_layout.addItem(QSpacerItem(0, 0))
        buttons_layout.addWidget(btn_create)
        buttons_layout.addWidget(btn_close)
        layout_main.addLayout(buttons_layout)
        self.layout = layout_main
        btn_create.clicked.connect(self.handle_create)
        btn_close.clicked.connect(self.handle_close)
        self.item = None
        self.item_created = Event()

    def close(self):
        self.handle_close()

    def handle_create(self):
        item = dict()
        if not self.txt_description.text.strip():
            Message_Box.warning(self, 'Error', 'item should contains a descriptin')
            return
        item.description = self.txt_description.text.strip()

        if self.txt_unit_measure.text.strip():
            item.unit_measure = self.txt_unit_measure.text.strip()

        if self.txt_lifetime.text.strip():
            item.lifetime = self.txt_lifetime.text.strip()

        if self.mass_edit.mass is not None :
            item.mass = self.mass_edit.mass
        msg = {'type_message': 'action', 'action': 'itzamara/create_item', 'item': item}
        codes_ref = self.code_ref_model.datasource

        if len(codes_ref) == 1:
            msg.code_ref = codes_ref[0]
        elif len(codes_ref) > 1:
            msg.codes_ref = codes_ref

        answer = agent_itzamara(msg)
        if 'error' in answer:
            Message_Box.warning(self, 'Error', 'Some error happened')
        elif 'item' in answer and answer.item is not None:
            Message_Box.information(self, 'Successfull', 'Item has been created')
            self.item_created(answer.item)
            self.item = answer.items
            Dialog.close(self)
        else:
            Message_Box.information(self, 'No created', 'Item was not created')


    def handle_close(self):
        if self.txt_description.text:
            r = Message_Box.question(self, 'Cerrar', 'Desea cerrar el dialog sin crear el articulo', Message_Box.Yes | Message_Box.No, Message_Box.No)
            if r == Message_Box.Yes:
                Dialog.close(self)
        else:
            Dialog.close(self)


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    d = Create_Item()
    d.show()
    sys.exit(app.exec_())
