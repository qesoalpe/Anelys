from PySide.QtGui import *
from PySide.QtCore import *
from isis.data_model.table import Table
from decimal import Decimal
from isis.table_view import Table_View

class Prices_Model(Table):
    def __init__(self):
        Table.__init__(self, 'Prices')
        self.columns.add('minimum', Decimal, '#,##0.###')
        self.columns.add('price', Decimal, 'c')
        self.columns.add('rate', Decimal, '#,##0.##')
        self.columns.add('benefit_minimum', Decimal, 'c')
        def getter_rate(row):
            if 'price' in row and self.cost is not None:
                return 100-(100/row.price) * self.cost

        def getter_benefit_minimum(row):
            if 'price' in row and 'minimum' in row and self.cost is not None:
                total_cost = row.minimum * self.cost
                total_amount = row.minimum * row.price
                return total_amount - total_cost

        self.columns['rate'].getter_data = getter_rate
        self.columns['benefit_minimum'].getter_data = getter_benefit_minimum
        self.cost = None
        self.datasource = list()
        self.with_new_empty_row = True

        self.columns['minimum'].changing_value = self.changing_value_minimum
        self.columns['price'].changing_value = self.changing_value_price
        self.columns['rate'].changing_value = self.changing_rate
        self.columns['benefit_minimum'].changing_value = self.changing_benefit_minimum

    def changing_value_minimum(self, i, value):
        row = self.datasource[i]
        if value is not None and value > 0:
            row.minimum = value
        elif 'minimum' in row:
            del row.minimum
        return True

    def changing_value_price(self, i, value):
        row = self.datasource[i]
        if value is not None and value > 0:
            row.price = value
        elif 'price' in row:
            del row.price
        return True

    def changing_rate(self, i, value):
        row = self.datasource[i]
        if value is not None and self.cost is not None:
            row.price = (self.cost / (100 - value)) * 100
        elif 'price' in row:
            del row.price
        return True

    def changing_benefit_minimum(self, i, value):
        row = self.datasource[i]
        if value is not None and self.cost is not None and 'price' in row and 'minimum' in row:
            total_cost = self.cost * row.minimim
            row.price = (total_cost + value)  / row.minimum
        return True




class Price_By_Scale(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        from isis.decimal_edit import Decimal_Edit
        from isis.label import Label
        lbl_cost = Label('cost', self)
        self.spn_cost = Decimal_Edit(self)
        self.tableview = Table_View(self)
        layoutmain = QGridLayout(self)
        layoutmain.addWidget(lbl_cost, 0, 0)
        layoutmain.addWidget(self.spn_cost, 0, 1)
        layoutmain.addWidget(self.tableview, 1, 0, 1, -1)
        self.setLayout(layoutmain)

        self.modelprices = Prices_Model()

        self.tableview.model = self.modelprices

        def handler(v):
            self.modelprices.cost = v

        self.spn_cost.value_changed.suscribe(handler)
        self.spn_cost.minimum = 0
        self.spn_cost.maximum = 99999
        self.spn_cost.value = 72


if __name__ == '__main__':
    from PySide.QtGui import QApplication
    import sys
    app = QApplication(sys.argv)
    vv = Price_By_Scale()
    vv.show()
    sys.exit(app.exec_())
