from isis.line_edit import Line_Edit
from datetime import datetime
from isodate import datetime_isoformat, parse_datetime

class Datetime_Edit(Line_Edit):
    def __init__(self, *args, **kwargs):
        Line_Edit.__init__(self, *args, **kwargs)
        self.setInputMask('9999-99-99T99:99;_')
        # self.text = datetime_isoformat(datetime.now())

    @property
    def value(self):
        try:
            from isodate import parse_datetime
            return parse_datetime(self.text)
        except:
            return None

    @value.setter
    def value(self, value):
        try:
            if isinstance(value, str):
                value = parse_datetime(value)

            assert isinstance(value, datetime)
            self.text = datetime_isoformat(value)
        except:
            self.text = None


if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    v = Datetime_Edit()
    v.value = '2017-08-05T02:30'
    v.show()
    sys.exit(app.exec_())
