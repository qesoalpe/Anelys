from PySide2.QtWidgets import QDialog
from isis.event import Event

pool_dialogs = list()


class Dialog(QDialog):
    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        self.closed = Event()
        self.shown = Event()
        self.___shownevent = False
        self._persist = True
        pool_dialogs.append(self)
        self.key_down = Event()
        self.close_with_escape = False
    #
    #
    # @property
    # def close_with_escape(self):
    #     return self._close_with_escape

    # @close_with_escape.setter
    # def close_with_escape(self, value):
    #     assert isinstance(value, bool)
    #     self._close_with_escape = value
    #     if value:
    #         self.reject = QDialog.reject
    #     else:
    #         self.reject = lambda : None

    def keyPressEvent(self, event):
        self.key_down(event)
        from PySide2.QtCore import Qt
        if event.key() == Qt.Key_Escape:
            if self.close_with_escape:
                QDialog.keyPressEvent(self, event)
            # else:
            #     event.ignore()
            #     QDialog.keyPressEvent(self, event)
            return
        QDialog.keyPressEvent(self, event)

    @property
    def persist(self):
        return self._persist

    @persist.setter
    def persist(self, persist):
        self._persist = persist
        if persist:
            pool_dialogs.append(self)
        else:
            if self in pool_dialogs:
                pool_dialogs.remove(self)

    def closeEvent(self, event):
        QDialog.closeEvent(self, event)
        self.closed()
        if self in pool_dialogs:
            pool_dialogs.remove(self)

    def showEvent(self, event):
        if not self.___shownevent:
            self.shown()
            self.___shownevent = True

    def handle_shown(self):
        pass

    @property
    def layout(self):
        return QDialog.layout(self)

    @layout.setter
    def layout(self, layout):
        QDialog.setLayout(self, layout)

    @property
    def window_title(self):
        return self.windowTitle()

    @window_title.setter
    def window_title(self, window_title):
        self.setWindowTitle(window_title)
