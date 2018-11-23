from PySide2.QtWidgets import QDoubleSpinBox
from isis.event import Event
from decimal import Decimal as D


class Decimal_Edit(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        QDoubleSpinBox.__init__(self, *args, **kwargs)
        self.setDecimals(2)
        self.setButtonSymbols(self.NoButtons)
        self.key_down = Event()
        self.value_changed = Event()
        def handle_value_changed(*args):
            self.value_changed(self.value)
        self.valueChanged.connect(handle_value_changed)

    @property
    def value(self):
        return round(D(QDoubleSpinBox.value(self)), self.decimals if hasattr(self, 'decimals') and not callable(self.decimals) else 6)

    @value.setter
    def value(self, value):
        if value is None:
            self.setValue(0)
        else:
            self.setValue(value)

    @property
    def maximum(self):
        return QDoubleSpinBox.maximum(self)

    @maximum.setter
    def maximum(self, maximum):
        self.setMaximum(maximum)

    @property
    def minimum(self):
        return QDoubleSpinBox.minimum(self)

    @minimum.setter
    def minimum(self, minimum):
        self.setMinimum(minimum)

    def keyPressEvent(self, event):
        QDoubleSpinBox.keyPressEvent(self, event)
        self.key_down(event)

    focus = QDoubleSpinBox.setFocus