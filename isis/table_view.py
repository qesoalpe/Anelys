from PySide2.QtWidgets import QTableView
from PySide2.QtCore import Qt
from isis.event import Event
from isis.menu import Menu
from PySide2.QtWidgets import QAction, QMenu


class Table_View(QTableView):
    def __init__(self, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)
        header = self.verticalHeader()
        # from PySide2.QtWidgets import QHeaderView
        header.setSectionResizeMode(header.Fixed)
        header.setDefaultSectionSize(20)
        self._edrws = False
        self.title_question_delete_row = None
        self.text_question_delete_row = None
        self.create_context_menu = Event()

    def setModel(self, model):
        QTableView.setModel(self, model)
        model.dataChanged.connect(self.resizeColumnsToContents)
        model.modelReset.connect(self.resizeColumnsToContents)
        model.rowsInserted.connect(self.resizeColumnsToContents)
        model.rowsRemoved.connect(self.resizeColumnsToContents)
        self.resizeColumnsToContents()

    @property
    def enable_delete_row_with_supr(self):
        return self._edrws

    @enable_delete_row_with_supr.setter
    def enable_delete_row_with_supr(self, value):
        self._edrws = value
        if value:
            pass
        else:
            pass

    def keyPressEvent(self, event):
        if self._edrws:
            if event.key() == Qt.Key_Delete:
                index = self.currentIndex()
                if index.isValid():
                    from isis.message_box import Message_Box
                    if self.title_question_delete_row is not None:
                        title = self.title_question_delete_row
                    else:
                        title = 'Delete Row'
                    if self.text_question_delete_row is not None:
                        text = self.text_question_delete_row
                    else:
                        text = 'You Want Delete Current Row??'
                    r = Message_Box.question(self, title, text, Message_Box.Yes | Message_Box.No, Message_Box.No)
                    if r == Message_Box.Yes:
                        if self.model is not None and hasattr(self.model, 'remove_row'):
                            self.model.remove_row(index.row())
            else:
                return QTableView.keyPressEvent(self, event)
        else:
            return QTableView.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if len(self.create_context_menu):
                index = self.indexAt(event.pos())
                if index.isValid():
                    model = self.model
                    from PySide2.QtCore import QSortFilterProxyModel
                    if isinstance(model, QSortFilterProxyModel):
                        index = model.mapToSource(index)
                        model = model.sourceModel()

                    item = model.datasource[index.row()]
                    column = model.columns[index.column()]
                    menu = self.create_context_menu(item, column)
                    if menu is not None:
                        if isinstance(menu, list):
                            the_menu = Menu(self)
                            # the_menu.addAction('this is a test')
                            for action in menu:
                                the_action = the_menu.addAction('')
                                for k, v in action.items():
                                    if k == 'text':
                                        the_action.setText(v)
                                    elif k == 'suscriber':
                                        the_action.triggered.connect(v)
                                    elif k == 'enabled':
                                        the_action.setEnabled(v)
                            the_menu.popup(event.globalPos())

        QTableView.mousePressEvent(self, event)

    @property
    def model(self):
        return QTableView.model(self)

    @model.setter
    def model(self, model):
        self.setModel(model)
