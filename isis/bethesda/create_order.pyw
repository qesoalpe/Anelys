from decimal import Decimal as D
from isis.itzamara.search_item import Search_Item as Search_Itzamara_Item
from sarah.acp_bson import Client
from isis.data_model.table import Table
from isis.widget import Widget
from isis.table_view import Table_View
from isis.label import Label
from isis.utils import format_currency
from isis.message_box import Message_Box
from isis.main_window import Main_Window
from isis.v_box_layout import V_Box_Layout
from isis.h_box_layout import H_Box_Layout
from isis.grid_layout import Grid_Layout
from PySide2.QtWidgets import QSpacerItem, QSizePolicy


class Table_Model_Items(Table):
    def __init__(self, parent_gui):
        Table.__init__(self)
        self.parent_gui = parent_gui
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', D, 'c')
        self.columns.add('amount', D, 'c')

        self.columns['sku'].changing_value = self.handle_changing_sku
        self.columns['quanty'].changing_value = self.handle_changing_quanty
        self.columns['description'].changing_value = self.handle_changing_description
        self.columns['price'].changing_value = self.handle_changing_price
        self.columns['amount'].changing_value = self.handle_changing_amount

        self.columns['amount'].getter_data = lambda x: x.quanty * x.price if 'price' in x and 'quanty' in x else None

        self.with_new_empty_row = True
        self.agent_itzamara = Client('', 'itzamara')

    def handle_changing_sku(self, i, value):
        row = self.datasource[i]
        if ('sku' not in row or row['sku'] != value) and value:
            msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': value}}
            answer = self.agent_itzamara.send_msg(msg)
            if 'result' in answer and answer['result'] is not None:
                result = answer['result']
                if 'sku' in result:
                    row['sku'] = result['sku']
                elif 'sku' in row:
                    del row['sku']
                if 'description' in result:
                    row['description'] = result['description']
                elif 'description' in row:
                    del row['description']
            elif 'sku' in row:
                del row.sku
        else:
            return False

    def handle_changing_quanty(self, i, value):
        item = self.datasource[i]
        if value is not None and value > 0:
            item['quanty'] = round(value, 3)
        elif 'quanty' in item:
            del item['quanty']
        else:
            return False

    def handle_changing_description(self, i, value):
        row = self.datasource[i]
        if 'description' not in row or row['description'] != value:
            searcher = Search_Itzamara_Item(self.parent_gui)
            result = searcher.search(value)
            if result is not None:
                if 'description' in result:
                    row['description'] = result['description']
                elif 'description' in row:
                    del row['description']
                if 'sku' in result:
                    row['sku'] = result['sku']
                elif 'sku' in row:
                    del row['sku']
            else:
                row['description'] = value
                if 'sku' in row: del row['sku']
        else:
            return False

    def handle_changing_price(self, i, value):
        item = self.datasource[i]
        if value is not None and value > 0:
            item['price'] = round(value, 2)
        elif 'price' in item:
            del item['price']
        else:
            return False

    def handle_changing_amount(self, i, value):
        item = self.datasource[i]
        if value is not None and value > 0 and 'quanty' in item:
            item['price'] = round(value / item['quanty'], 2)
        elif 'price' in item:
            del item['price']
        else:
            return False

    @property
    def total(self):
        total = D()
        for item in self.datasource:
            if 'quanty' in item and 'price' in item:
                total += round(item.quanty * item.price, 2)
        return total


class Table_View_Items(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.enable_delete_row_with_supr = True


class Create_Order(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(900, 500)
        self.cwidget = Widget(self)
        self.setCentralWidget(self.cwidget)
        self.setWindowTitle(self.__class__.__name__)
        from isis.piper.widget_viewer_provider import Widget_Viewer_Provider
        from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage

        lbl_amount = Label('amount: ', self.cwidget)
        lbl_arrive = Label('arrive: ', self.cwidget)
        self.lbl_amount = Label(self.cwidget)
        from isis.line_edit import Line_Edit
        self.txt_arrive = Line_Edit(self.cwidget)

        self.widget_provider = Widget_Viewer_Provider(self.cwidget)
        self.widget_storage = Widget_Viewer_Storage(self.cwidget)

        self.tableview = Table_View_Items(self.cwidget)

        self.model = Table_Model_Items(self)
        self.tableview.model = self.model

        lbl_amount.fix_size_based_on_font()
        lbl_arrive.fix_size_based_on_font()
        self.txt_arrive.setFixedWidth(self.txt_arrive.fontMetrics().width('xxxx-xx-xxTxx:xx:xx'))
        layout_main = V_Box_Layout(self.cwidget)

        layout_header = H_Box_Layout()
        layout_summary = Grid_Layout()
        layout_summary.addWidget(lbl_amount, 0, 0)
        layout_summary.addWidget(self.lbl_amount, 0, 1)
        layout_summary.addWidget(lbl_arrive, 1, 0)
        layout_summary.addWidget(self.txt_arrive, 1, 1)
        layout_summary.addItem(QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Preferred), 2, 0, -1, -1)

        layout_header.addLayout(layout_summary)

        layout_header.addWidget(self.widget_provider)
        layout_header.addWidget(self.widget_storage)

        layout_main.addLayout(layout_header)
        layout_main.addWidget(self.tableview)

        self.widget_storage.with_button_change = True
        self.widget_provider.with_button_change = True
        self.cwidget.setLayout(layout_main)

        self.model.any_change_in_datasource.suscribe(self.update_value)
        self.update_value()

        tool_bar = self.addToolBar('file')
        create = tool_bar.addAction('create')
        create.triggered.connect(self.handle_create)

    def update_value(self, *args):
        self.lbl_amount.text = format_currency(self.model.total)

    def handle_create(self):
        from dict import Dict
        from copy import deepcopy
        from datetime import datetime
        order = Dict()
        order['items'] = list(filter(lambda x: 'description' in x and 'quanty' in x, deepcopy(self.model.datasource)))
        if self.txt_arrive.text:
            order.arrive = self.txt_arrive.text
        from isodate import datetime_isoformat
        order.datetime = datetime_isoformat(datetime.now())
        if self.widget_provider.provider is not None:
            order.provider = self.widget_provider.provider
        else:
            Message_Box.warning(self, 'error', 'order should contains a provider')
            return
        if self.widget_storage.storage is not None:
            order.storage = self.widget_storage.storage
        else:
            Message_Box.warning(self, 'error', 'order should contains a storage')
            return
        order.amount = self.model.total

        msg = {'type_message': 'action', 'action': 'bethesda/create_order', 'order': order}
        agent_bethesda = Client('', 'bethesda')
        answer = agent_bethesda.send_msg(msg)
        if 'order' in answer:
            Message_Box.information(self, 'created', 'bethesda/order has been created.')
            self.close()
        else:
            Message_Box.warning(self, 'no created', 'behtesda/order has not been created')


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Create_Order()
    vv.show()
    sys.exit(app.exec_())
