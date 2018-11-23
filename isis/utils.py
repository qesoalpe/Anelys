from PySide2.QtGui import QFont
from babel import numbers
from decimal import Decimal as D
from isis.label import Label


LOCALE_DEFAULT = 'es_mx'


def set_label_fixed_width_based_font_metrics(ww):
    if isinstance(ww, Label):
        ww.setFixedWidth(ww.fontMetrics().width(ww.text))
    else:
        ww.setFixedWidth(ww.fontMetrics().width(ww.text()))

h1_font = QFont()
h1_font.setPointSize(14)
h1_font.setBold(True)


def format_currency(number):
    try:
        return numbers.format_currency(number, 'MXN', locale=LOCALE_DEFAULT)
    except:
        return None


def format_number(number):
    return numbers.format_decimal(number, locale=LOCALE_DEFAULT)


def parse_number(number):
    text_number = number.replace('$', '')
    try:
        return D(text_number)
    except:
        pass

    try:
        return numbers.parse_decimal(text_number, locale=LOCALE_DEFAULT)
    except:
        pass

    return None
