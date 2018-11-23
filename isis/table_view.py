from PySide2.QtWidgets import QTableView


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
            from PySide2.QtCore import Qt
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

    @property
    def model(self):
        return QTableView.model(self)

    @model.setter
    def model(self, model):
        self.setModel(model)
