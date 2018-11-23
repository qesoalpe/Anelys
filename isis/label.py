from PySide2.QtWidgets import QLabel


class Label(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)


    @property
    def text(self):
        return QLabel.text(self)

    @text.setter
    def text(self, text):
        self.setText(text)

    def fix_size_based_on_font(self):
        self.setFixedWidth(self.fontMetrics().width(self.text))
