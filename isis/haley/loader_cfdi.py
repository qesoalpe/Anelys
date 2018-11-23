from sarah.acp_bson import Client
from isis.haley.select_cfdi_no_attached import Select_Cfdi_No_Attached
from isis.push_button import Push_Button
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.grid_layout import Grid_Layout
from isis.dialog import Dialog
from isis.file_dialog import File_Dialog
from isis.message_box import Message_Box


class Loader_Cfdi(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.setWindowTitle('Loader_Cfdi')
        lbl_uuid = Label('uuid: ', self)
        self.txt_uuid = Line_Edit(self)
        btn_search_uuid = Push_Button('search', self)
        btn_select_file_xml = Push_Button('select from filesystem host katherine', self)
        btn_select_from_cfdis_no_attached = Push_Button('select_from_cfdis_no_attached', self)

        lbl_uuid.fix_size_based_on_font()

        self.txt_uuid.setFixedWidth(self.txt_uuid.fontMetrics().width('550e8400-e29b-41d4-a716-446655440000xxx'))
        self.txt_uuid.setMaxLength(len('550e8400-e29b-41d4-a716-446655440000'))
        mainlayout = Grid_Layout(self)
        mainlayout.addWidget(btn_select_from_cfdis_no_attached, 0, 0, 1, -1)
        mainlayout.addWidget(lbl_uuid, 1, 0)
        mainlayout.addWidget(self.txt_uuid, 1, 1)
        mainlayout.addWidget(btn_search_uuid, 1, 2)
        mainlayout.addWidget(btn_select_file_xml, 1, 0, 1, -1)

        self.cfdi = None

        self.agent_haley = Client('isis.bethesda.create_document', 'haley')
        btn_search_uuid.clicked.connect(self.handle_btn_search_uuid_clicked)
        btn_select_file_xml.clicked.connect(self.handle_btn_select_file_xml_clicked)
        btn_select_from_cfdis_no_attached.clicked.connect(self.handle_btn_select_from_cfdis_no_attached_clicked)

    def handle_btn_search_uuid_clicked(self):
        uuid = self.txt_uuid.text().upper()
        msg = {'type_message': 'find_one', 'type': 'haley/cfdi', 'query': {'uuid': uuid}}
        answer = self.agent_haley(msg)
        if 'result' in answer and answer['result'] is not None:
            self.cfdi = answer['result']
            self.close()
        else:
            Message_Box.information(self, 'not found', 'no se encontro cfdi with thah uuid')

    def handle_btn_select_file_xml_clicked(self):
        filename = File_Dialog.getOpenFileName(self, 'select cfdi xml', '.', 'xml (*.xml)')[0]
        if filename:
            f = open(filename, 'rt', encoding='utf8')
            xmlstring = f.read()
            f.close()
            msg = {'type_message': 'action', 'action': 'haley/parse_cfdi_xml', 'persist': True,
                   'cfdi_type': 'xmlstring', 'cfdi': xmlstring}
            answer = self.agent_haley(msg)
            self.cfdi = answer['cfdi']
            self.close()

    def handle_btn_select_from_cfdis_no_attached_clicked(self):
        selecter = Select_Cfdi_No_Attached(self)
        selecter.exec_()
        if selecter.selected is not None:
            self.cfdi = selecter.selected
            self.close()
