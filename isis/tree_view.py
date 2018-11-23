from PySide.QtGui import QTreeView
from PySide.QtCore import Qt
from isis.event import Event

class Tree_View(QTreeView):
    def __init__(self, *args, **kwargs):
        QTreeView.__init__(self, *args, **kwargs)
        self.double_clicked = Event()

    def resizeColumnsToContents(self, *args, **kwargs):
        if self.model is not None:
            for i in range(0, self.model.columnCount()):
                self.resizeColumnToContents(i)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                self.double_clicked(index)


    @property
    def model(self):
        return QTreeView.model(self)

    @model.setter
    def model(self, model):
        QTreeView.setModel(self, model)
        model.dataChanged.connect(self.resizeColumnsToContents)
        model.modelReset.connect(self.resizeColumnsToContents)
        model.rowsInserted.connect(self.resizeColumnsToContents)
        model.rowsRemoved.connect(self.resizeColumnsToContents)
        self.resizeColumnsToContents()
