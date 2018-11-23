from PySide2.QtWidgets import QWidget


class Widget(QWidget):
    @property
    def layout(self):
        return QWidget.layout(self)

    @layout.setter
    def layout(self, layout):
        QWidget.setLayout(self, layout)