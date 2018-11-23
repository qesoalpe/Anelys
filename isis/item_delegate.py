from PySide.QtGui import QStyledItemDelegate, QDoubleSpinBox, QAbstractSpinBox
from PySide.QtCore import Qt
from decimal import Decimal

class Double_Spin_Edit(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
    def interpretText(self):
        if not self.text():
            self.setValue(0)
        else:
            QDoubleSpinBox.interpretText(self)


class Money_Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setPrefix('$')
        editor.setButtonSymbols(QAbstractSpinBox.NoButtons)
        editor.setMaximum(100000000)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        assert isinstance(editor, QDoubleSpinBox)
        if value is None:
            editor.setValue(0)
        else:
            editor.setValue(value)

    def setModelData(self, editor, model, index):
        assert isinstance(editor, QDoubleSpinBox)
        editor.interpretText()
        model.setData(index, round(Decimal(editor.value()), 6), Qt.EditRole)


class Decimal_Delegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(-100000000)
        editor.setButtonSymbols(QAbstractSpinBox.NoButtons)
        editor.setMaximum(100000000)
        editor.setDecimals(3)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        assert isinstance(editor, QDoubleSpinBox)
        if value is None:
            editor.setValue(0)
        else:
            editor.setValue(value)

    def setModelData(self, editor, model, index):
        # editor.interpretText()
        value = Decimal(editor.value())
        # print(value)
        model.setData(index, round(value, 6), Qt.EditRole)
