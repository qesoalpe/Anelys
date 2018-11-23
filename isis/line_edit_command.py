from isis.line_edit import Line_Edit
from PySide2.QtCore import Qt
from isis.event import Event


class Line_Edit_Command(Line_Edit):
    def __init__(self, *args, **kwargs):
        Line_Edit.__init__(self, *args, **kwargs)
        self.command = Event()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.command(self.text)
            self.text = None
        elif event.key() == Qt.Key_Escape:
            self.text = ''
        else:
            Line_Edit.keyPressEvent(self, event)

