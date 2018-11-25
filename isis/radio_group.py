from PySide.QtGui import QGroupBox, QRadioButton, QVBoxLayout


class Item():
    def __init__(self, parentwidget):
        self.value = None
        self.radiobutton = QRadioButton(parentwidget)

    @property
    def description(self):
        return self.radiobutton.text()

    @description.setter
    def description(self, description):
        self.radiobutton.setText(description)

class Items(list):
    def __init__(self):
        list.__init__(self)
        self.parentwidget = None
        self.radiogroup = None

    def add(self, description, value):
        item = Item(self.parentwidget)
        item.description = description
        item.value = value
        self.append(item)
        radiogroup = self.radiogroup
        layout = radiogroup.layout()
        c = layout.count()
        layout.insertWidget(c, item.radiobutton)

        return item


class Radio_Group(QGroupBox):
    def __init__(self, *args, **kwargs):
        QGroupBox.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().addStretch(1)
        self.items = Items()
        self.items.parentwidget = self
        self.items.radiogroup = self
        # {value: <value>, radio: QRadioButton, description,

    @property
    def value(self):
        for item in self.items:
            if item.radiobutton.isChecked():
                return item.value
        else:
            return None

    @value.setter
    def value(self, value):
        for item in self.items:
            if value is None:
                if item.value is None:
                    item.radiobutton.setChecked(True)
                    break
            elif item.value is not None and item.value == value:
                item.radiobutton.setChecked(True)
                break
        else:
            raise ValueError(value)
