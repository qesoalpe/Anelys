from isis.push_button import Push_Button
from isis.table_view import Table_View
from isis.h_box_layout import H_Box_Layout
from isis.v_box_layout import V_Box_Layout
from PySide2.QtWidgets import QSizePolicy
from isis.event import Event
from isis.dialog import Dialog
from dict import Dict as dict, List as list
from PySide2.QtCore import Qt
from isis.data_model.table import Table


class Dialog_Select_Table(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Dialog_Select_Table')
        self.resize(700, 400)
        self.tableview = Table_View(self)
        btn_select = Push_Button('select', self)
        btn_close = Push_Button('close', self)
        self.tableview.setSelectionMode(Table_View.SingleSelection)
        self.tableview.setSelectionBehavior(Table_View.SelectRows)
        self.tableview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.mainlayout = V_Box_Layout(self)
        self.mainlayout.addWidget(self.tableview)
        self.button_layout = H_Box_Layout()
        self.button_layout.addWidget(btn_select)
        self.button_layout.addWidget(btn_close)
        self.mainlayout.addItem(self.button_layout)
        self.setLayout(self.mainlayout)
        self.tableview.doubleClicked.connect(self.tableview_doubleClicked)
        self.selectablelist = None
        self._selected = None
        self.tableview.doubleClicked.connect(self.tableview_doubleClicked)
        btn_select.clicked.connect(self.handle_btn_select_clicked)
        btn_close.clicked.connect(self.close)
        # the magic
        e = dict()
        self.loading(e)
        if 'table' in e and isinstance(e.table, Table):
            e.table.readonly = True

        if 'list' in e:
            self.selectablelist = e['list']
        else:
            self.selectablelist = None
        if 'table' in e:
            self.tableview.setModel(e['table'])
            if self.tableview.model.rowCount() >= 1:
                self.tableview.selectRow(0)
        self.tableview.resizeColumnsToContents()
        self.tableview.setFocus()
        self.item_selected = Event()
        self.loaded = Event()

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected):
        self._selected = selected
        if selected is not None:
            self.item_selected(selected)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if self.tableview.hasFocus():
                index = self.tableview.currentIndex()
                if index.isValid():
                    if hasattr(self, 'selecting') and self.selecting is not None:
                        self.selected = self.selecting(index.row())
                    else:
                        self.selected = self.selectablelist[index.row()]
                    self.close()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            if self.tableview.hasFocus():
                self.close()
            event.accept()

    def tableview_doubleClicked(self, index):
        if index.isValid():
            if hasattr(self, 'selecting') and self.selecting is not None:
                self.selected = self.selecting(index.row())
            else:
                self.selected = self.selectablelist[index.row()]
            self.close()

    def handle_btn_select_clicked(self):
        index = self.tableview.currentIndex()
        if index.isValid():
            if hasattr(self, 'selecting') and self.selecting is not None:
                self.selected = self.selecting(index.row())
            else:
                self.selected = self.selectablelist[index.row()]
            self.close()

    def loading(self, e):
        pass

