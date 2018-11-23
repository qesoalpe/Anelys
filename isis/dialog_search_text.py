from PySide2.QtWidgets import QSizePolicy
from PySide2.QtGui import QKeyEvent
from PySide2.QtCore import Qt
from decimal import Decimal as D
from isis.utils import format_currency
from dict import Dict as dict, List as list
from isis.event import Event
from isis.data_model.table import Table
from isis.dialog import Dialog
from isis.line_edit import Line_Edit
from isis.table_view import Table_View
from isis.push_button import Push_Button
from isis.application import Application
from isis.message_box import Message_Box
from isis.h_box_layout import H_Box_Layout
from isis.v_box_layout import V_Box_Layout
from isis.label import Label


class Dialog_Search_Text(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.resize(450, 550)
        self.setWindowTitle('Dialog_Search_Text')
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        lbl_search = Label('Buscar ', self)

        self.txt_search = Line_Edit(self)
        self.searchlayout = H_Box_Layout()
        self.searchlayout.addWidget(lbl_search)
        lbl_search.fix_size_based_on_font()
        self.searchlayout.addWidget(self.txt_search)
        self.tableview = Table_View(self)
        self.tableview.setSelectionMode(Table_View.SingleSelection)
        self.tableview.setSelectionBehavior(Table_View.SelectRows)
        self.txt_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tableview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.btn_accept = Push_Button('Aceptar', self)
        self.btn_close = Push_Button('Cerrar', self)
        self.mainlayout = V_Box_Layout(self)
        self.mainlayout.addItem(self.searchlayout)
        self.mainlayout.addWidget(self.tableview)
        self.button_layout = H_Box_Layout()
        self.button_layout.addWidget(self.btn_accept)
        self.button_layout.addWidget(self.btn_close)
        self.mainlayout.addItem(self.button_layout)
        self.btn_close.clicked.connect(self.close)
        self.setLayout(self.mainlayout)
        self.item_selected = Event()
        self.tableview.doubleClicked.connect(self.tableview_doubleClicked)
        self._selected = None
        self.selectablelist = None

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected):
        if selected is not None:
            self.item_selected(selected)
        self._selected = selected

        def handler_accept_clicked():
            index = self.tableview.currentIndex()
            if index.isValid():
                self.selected = self.selectablelist[index.row()]
                self.close()

        self.btn_accept.clicked.connect(handler_accept_clicked)
        # self.btn_accept.setDefault(True)
        self.txt_search.setFocus()

    def keyPressEvent(self, event):
        assert isinstance(event, QKeyEvent)
        if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            if self.txt_search.hasFocus():
                self.search(self.txt_search.text)
            elif self.tableview.hasFocus():
                index = self.tableview.currentIndex()
                if index.isValid():
                    self.selected = self.selectablelist[index.row()]
                    self.close()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            if self.txt_search.hasFocus():
                if self.txt_search.text:
                    self.txt_search.text = None
                else:
                    self.close()
            elif self.tableview.hasFocus():
                self.txt_search.setFocus()
                self.txt_search.selectAll()
            event.accept()

    def searching(self, e):
        pass
        # e:= {text: txt, listtoselect: list(),

    def search(self, text_search, parent=None):
        self.selected = None
        e = dict({'text': text_search})
        self.searching(e)
        if hasattr(self, 'after_searching'):
            self.after_searching(e)

        if 'selected' in e:
            self.selected = e['selected']
            if self.isVisible():
                self.close()
            return self.selected

        if 'list' in e:
            self.selectablelist = e.list
        else:
            self.selectablelist = None

        from isis.data_model.table import Table
        if isinstance(e.table, Table):
            e.table.readonly = True

        self.tableview.model = e.table

        if self.tableview.model.rowCount() == 1:
            self.selected = self.selectablelist[0]
            if self.isVisible():
                self.close()
            return self.selected

        elif self.tableview.model.rowCount() > 1:
            self.tableview.selectRow(0)
        elif self.tableview.model.rowCount() == 0:
            if parent is not None:
                ownermsgbox = parent
            else:
                ownermsgbox = self
            Message_Box.information(ownermsgbox, ownermsgbox.windowTitle(), 'No se encontraron resultados')
            if not self.isVisible():
                return self.selected
        self.tableview.resizeColumnsToContents()
        self.selected = None
        if not self.isVisible():
            self.txt_search.setText(text_search)
            # self.txt_search.setCursorPosition(len(text_search))
            self.tableview.setFocus()
            self.exec_()
            return self.selected
        else:
            self.tableview.setFocus()

    def tableview_doubleClicked(self, index):
        if index.isValid():
            self.selected = self.selectablelist[index.row()]
            self.close()


if __name__ == '__main__':
    import sys
    app = Application(sys.argv)
    vv = Dialog_Search_Text()
    vv.exec_()
    # sys.exit(app.exec_())
