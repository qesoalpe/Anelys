from sarah.acp_bson import Client
from isis.bailey.charge_check import Charger
from isis.data_model.table import Table
from decimal import Decimal as D
from isis.table_view import Table_View
from isis.menu import Menu
from isis.main_window import Main_Window
from isis.v_box_layout import V_Box_Layout
from isis.widget import Widget

from PySide2.QtCore import Qt

class Model_Checks(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('number', int)
        self.columns.add('date', str)
        self.columns.add('amount', D, 'c')
        self.columns.add('beneficiary', str)
        self.columns.add('status', str)
        self.readonly = True

        def getter_beneficiaty(data):
            if 'beneficiary' in data:
                ben = data.beneficiary
                if 'business_name' in ben:
                    return ben.business_name
                elif 'name' in ben:
                    return ben.name
                elif 'rfc' in ben:
                    return ben.rfc
                elif 'id' in ben:
                    return ben.id
                else:
                    return ben
        self.columns['beneficiary'].getter_data = getter_beneficiaty


class Table_View_Checks(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.handle_check_charge = None
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)

    def mousePressEvent(self, event):
        Table_View.mousePressEvent(self, event)
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                row = self.model.datasource[index.row()]
                if 'status' in row and row['status'] in ['delivered', 'elaborated']:
                    menu = Menu(self)
                    action_charge = menu.addAction('charge_check')
                    def handle_charge():
                        if self.handle_check_charge is not None:
                            self.handle_check_charge(index.row())
                    action_charge.triggered.connect(handle_charge)
                    menu.popup(event.globalPos())
                    return True
        return False


class Checks(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(600, 250)
        self.setWindowTitle('Checks')
        self.cwidget = Widget(self)
        self.setCentralWidget(self.cwidget)
        self.tableview = Table_View_Checks(self.cwidget)

        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addWidget(self.tableview)
        self.cwidget.setLayout(layoutmain)
        self.modelchecks = Model_Checks()
        self.tableview.setModel(self.modelchecks)
        self._checks = None
        self.tableview.handle_check_charge = self.handle_tableview_check_charge
        self.agent_bailey = Client('Checks', 'bailey')
        answer = self.agent_bailey({'type_message': 'find', 'type': 'bailey/check',
                                    'query': {'status': {'!nin': ['canceled','charged']}}})
        if 'result' in answer and answer['result'] is not None:
            answer.result.sort(key=lambda x: x.number)
            self.checks = answer['result']


    @property
    def checks(self):
        return self._checks

    @checks.setter
    def checks(self, x):
        self._checks = x
        self.modelchecks.datasource = self._checks

    def handle_tableview_check_charge(self, index):
        charger = Charger(self)
        charger.check = self.checks[index]
        charger.exec_()
        if charger.check is not None and 'status' in charger.check and charger.check['status'] == 'charged':
            self.modelchecks.remove_row(index)


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Checks()
    vv.show()
    sys.exit(app.exec_())
