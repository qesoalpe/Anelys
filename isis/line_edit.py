from PySide2.QtWidgets import QLineEdit, QDoubleSpinBox
from PySide2.QtGui import QKeyEvent
from PySide2.QtCore import QTimer, Qt
from decimal import Decimal
from babel.numbers import format_currency, format_decimal, format_number
from isis.event import Event


class Line_Edit(QLineEdit):
    def __init__(self, parent=None, timeoutdelayediting=0):
        QLineEdit.__init__(self, parent)
        self.handler_text_edited = None
        self.timer_typing = QTimer(self)
        self.timer_typing.setSingleShot(True)
        self.timer_typing.timeout.connect(self._handle_text_edited_with_delay)
        self.timeoutdelayediting = timeoutdelayediting
        self.textEdited.connect(self._handle_text_edited)

        self.editingFinished.connect(self._handle_editing_finished)

        self.key_down = Event()
        self.text_edited = Event()

    def _handle_editing_finished(self):
        self.timer_typing.stop()

    def _handle_text_edited(self):
        self.timer_typing.start(self.timeoutdelayediting)

    def _handle_text_edited_with_delay(self):
        if self.handler_text_edited is not None:
            self.handler_text_edited(self.text)
        self.text_edited(self.text)

    @property
    def text(self):
        return QLineEdit.text(self)

    @text.setter
    def text(self, text):
        if text is not None:
            self.setText(text)
        else:
            self.setText('')

    def keyPressEvent(self, event):
        QLineEdit.keyPressEvent(self, event)
        self.key_down(event)

    focus = QLineEdit.setFocus


class Spin_Edit(QDoubleSpinBox):
    def closeEvent(self, event):
        if not self.text():
            self.setValue(0)
            event.accept()

    def focusOutEvent(self, event):
        print('focusoutevent')
        print(self.text())
        if not self.text():
            self.setValue(0)
            print('focusoutevent_2')
        QDoubleSpinBox.focusOutEvent(self, event)

class mark_2(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self._decimals = 2
    @property
    def decimals(self):
        return self._decimals

    @decimals.setter
    def decimals(self, dd):
        self._decimals = dd

    @property
    def value(self):
        if self.text():
            return Decimal(self.text())
        else:
            return None
    @value.setter
    def value(self, x):
        self.pattern = '#,##0'
        if self._decimals > 0:
            self.patter += '.' + '#'

        self.setText(format_decimal(x, self.pattern, 'es_mx'))

    def keyPressEvent(self, event):
        curr_pos = self.cursorPosition()
        def __help(char):

            pos = self.cursorPosition()
            text = self.text()
            dotpos = text.find('.')
            if dotpos > 0 and pos > dotpos and self._decimals is not None and self._decimals >= 0:
                pass
            text = text[:pos] + char + text[pos:]
            self.setText(text)
            self.setCursorPosition(pos + 1)
            # self.cursorForward(False)
        handle_char_dict = {Qt.Key_0: '0', Qt.Key_1: '1', Qt.Key_2: '2', Qt.Key_3: '3', Qt.Key_4: '4', Qt.Key_5: '5',
                            Qt.Key_6: '6', Qt.Key_7: '7', Qt.Key_8: '8', Qt.Key_9: '9'}
        if event.key() in handle_char_dict:
            __help(handle_char_dict[event.key()])
        elif event.key() == Qt.Key_Left:
            self.cursorBackward(False)
        elif event.key() == Qt.Key_Right:
            self.cursorForward(False)
        elif event.key() == Qt.Key_Minus:
            text = self.text()
            if len(text) > 0 and text[0] == '-':
                if len(text) > 1:
                    self.setText(text[1:])
                    self.setCursorPosition(curr_pos - 1)
            else:
                self.setText('-' + text)
                self.setCursorPosition(curr_pos + 1)
        elif event.key() == Qt.Key_Period:
            text = self.text()
            if '.' not in text:
                __help('.')
        elif event.key() == Qt.Key_Backspace:
            text = self.text()
            if curr_pos > 0:
                text = text[:curr_pos -1] + text[curr_pos:]
                self.setText(text)
                self.setCursorPosition(curr_pos - 1)
        elif event.key() == Qt.Key_Delete:
            text = self.text()
            if curr_pos < len(text):
                text = text[:curr_pos] + text[curr_pos + 1:]
                self.setText(text)
                self.setCursorPosition(curr_pos)
        elif event.key() == Qt.Key_End:
            self.setCursorPosition(len(self.text()))
        elif event.key() == Qt.Key_Home:
            self.setCursorPosition(0)
        if self.text():
            self._value = Decimal(self.text())
        else:
            self._value = None






if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = mark_2()
    vv.show()
    sys.exit(app.exec_())