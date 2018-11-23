from isis.main_window import Main_Window
from isis.widget import Widget
from sarah.acp_bson import Client
from decimal import Decimal
from isis.utils import format_currency
from isis.data_model.table import Table, Event
from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
from isis.table_view import Table_View
from isis.label import Label
from isis.dialog import Dialog
from isis.grid_layout import Grid_Layout
from isis.v_box_layout import V_Box_Layout


class Model_Items(Table):
    def __init__(self):
        Table.__init__(self, 'items')
        self.readonly = True
        self.columns.add('sku', str)
        self.columns.add('quanty', Decimal, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', Decimal, 'c')
        self.columns.add('amount', Decimal, 'c')
        self.columns['amount'].getter_data = lambda x: format_currency(x['quanty'] * x['price'])


class Viewer_Order(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Viewer_Order')
        self.resize(700, 500)
        lbl_id = Label('id: ', self)
        lbl_datetime = Label('datetime: ', self)
        lbl_amount = Label('amount: ', self)
        lbl_status = Label('status: ', self)
        lbl_arrives = Label('arrives: ', self)

        self.lbl_id = Label(self)
        self.lbl_datetime = Label(self)
        self.lbl_amount = Label(self)
        self.lbl_status = Label(self)
        self.lbl_arrives = Label(self)

        self.viewer_provider = Widget_Viewer_Provider(self)
        self.viewer_storage = Widget_Viewer_Storage(self)

        self.tableview = Table_View(self)
        self.model = Model_Items()
        self.tableview.model = self.model
        headerlayout = Grid_Layout()
        headerlayout.addWidget(lbl_id, 0, 0)
        headerlayout.addWidget(self.lbl_id, 0, 1)
        headerlayout.addWidget(lbl_datetime, 0, 2)
        headerlayout.addWidget(self.lbl_datetime, 0, 3)
        headerlayout.addWidget(lbl_status, 1, 0)
        headerlayout.addWidget(self.lbl_status, 1, 1)
        headerlayout.addWidget(lbl_arrives, 1, 2)
        headerlayout.addWidget(self.lbl_arrives, 1, 3)
        headerlayout.addWidget(lbl_amount, 2, 0)
        headerlayout.addWidget(self.lbl_amount, 2, 1)
        headerlayout.addWidget(self.viewer_provider, 0, 4, -1, 1)
        headerlayout.addWidget(self.viewer_storage, 0, 5, -1, 1)
        layoutmain = V_Box_Layout(self)
        layoutmain.addLayout(headerlayout)
        layoutmain.addWidget(self.tableview)

        self._order = None
        self._items = None
        # self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.closed = Event()

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, order):
        self._order = order
        if order is not None:
            self.viewer_provider.provider = order['provider'] if 'provider' in order else None
            self.viewer_storage.storage = order['storage'] if 'storage' in order else None
            self.model.datasource = order['items'] if 'items' in order else None
            self.lbl_id.text = order['id'] if 'id' in order else None
            if 'amount' in order:
                from isis.utils import format_currency as f_c
                self.lbl_amount.text = f_c(order.amount)
            else:
                self.lbl_amount.text = None

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items
        self.model.datasource = items

    def closeEvent(self, *args, **kwargs):
        self.closed(self)


class Model_Table_Orders(Table):
    def __init__(self):
        Table.__init__(self, 'orders')
        self.columns.add('id', str)
        self.columns.add('datetime', str)
        self.columns.add('provider', str)
        self.columns.add('amount', Decimal, 'c')
        self.columns.add('storage', str)
        self.columns.add('status', str)
        self.columns.add('arrive', str)

        def get_provider(data):
            if 'provider' in data:
                provider = data['provider']
                if 'business_name' in provider:
                    return provider['business_name']
                elif 'name' in provider:
                    return provider['name']
                elif 'rfc' in provider:
                    return provider['rfc']
        self.columns['provider'].getter_data = get_provider
        self.columns['amount'].getter_data = ['amount', 'total']

        def get_storage(data):
            if 'storage' in data:
                storage = data.storage
                if isinstance(storage, dict):
                    if 'name' in storage:
                        return storage.name
                    elif 'address' in storage:
                        return storage.address
                    elif 'id' in storage:
                        return storage.id
                else:
                    return storage
        self.columns['storage'].getter_data = get_storage
        self.readonly = True


class Table_View_Orders(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)

    def mouseDoubleClickEvent(self, e):
        from PySide2.QtGui import QMouseEvent
        from PySide2.QtCore import Qt
        assert isinstance(e, QMouseEvent)
        if e.button() == Qt.LeftButton:
            i = self.indexAt(e.pos())
            if i.isValid():

                viewer = Viewer_Order()

                viewer.order = self.model.datasource[i.row()]
                viewer.show()

        Table_View.mouseDoubleClickEvent(self, e)


class Orders(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(850, 600)
        self.setWindowTitle('Orders')
        self.cwidget = Widget(self)

        # from pymongo import MongoClient
        from dict import Dict
        # d1 = MongoClient('mongodb://comercialpicazo.com', document_class=Dict)
        # d1.admin.authenticate('alejandro', '47exI4')
        # orders = [order for order in
        #           d1.bethesda.order.find({'status': 'to_receive'}, {'_id': False}).sort('datetime', -1).limit(50)]

        self.agentbethesda = Client('isis.bethesda_orders', 'bethesda')
        # msg = {'type_message': 'find', 'type': 'bethesda/order', 'query': {'status': 'to_receive'},
        #        'sort': [['datetime', -1]], 'limit': 50}
        msg = {'type_message': 'find', 'type': 'bethesda/order', 'query': {'status': 'to_receive'},
               'sort': {'datetime': -1}, 'limit': 50}
        answer = self.agentbethesda.send_msg(msg)
        orders = answer['result']

        self.modeltable = Model_Table_Orders()
        self.modeltable.datasource = orders

        self.tableview = Table_View_Orders(self.cwidget)
        self.tableview.setModel(self.modeltable)
        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addWidget(self.tableview)
        self.cwidget.setLayout(layoutmain)


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    vv = Orders()
    vv.show()
    sys.exit(app.exec_())
