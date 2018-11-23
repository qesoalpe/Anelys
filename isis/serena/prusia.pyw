from decimal import Decimal, Decimal as D
from isis.utils import format_currency
from sarah.acp_bson import Client
from isis.serena.search_product import Search_Product
from isis.dialog_select_table import Dialog_Select_Table
from pymongo import MongoClient
from isis.table_view import Table_View
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.push_button import Push_Button
from isis.v_box_layout import V_Box_Layout
from isis.h_box_layout import H_Box_Layout
from isis.main_window import Main_Window
from isis.widget import Widget
from dict import Dict, Dict as dict, List as list
from isis.event import Event
from utils import find_one
from isis.data_model.table import Table
from isis.caroline.widget_client import Widget_Client
from isodate import datetime_isoformat
from datetime import datetime
from copy import deepcopy
import dictutils
from isis.dialog import Dialog
from PySide2.QtCore import Qt, QEvent
from PySide2.QtGui import QFont
from isis.message_box import Message_Box
from PySide2.QtGui import QKeyEvent


APP_ID = '31-10'

local_mongo = MongoClient(port=27020, document_class=Dict)
app_db = local_mongo.get_database(APP_ID)
coll_sales_saved = app_db.get_collection('sales_saved')


class Select_Sale_Local_Saved(Dialog_Select_Table):
    def __init__(self, parent=None):
        self.coll_sales_saved = coll_sales_saved
        Dialog_Select_Table.__init__(self, parent)
        self.item_selected.suscribe(self.handle_selected)

    def handle_selected(self, selected):
        if '_id' in selected:
            self.coll_sales_saved.remove({'_id': selected._id})
            del selected._id

    def loading(self, e):
        result = list(self.coll_sales_saved.find().sort('datetime', -1))
        dictutils.list_float_to_dec(result)

        table = Table()
        table.columns.add('datetime', str)
        table.columns.add('client', str)
        table.columns.add('amount', Decimal, 'c')
        table.readonly = True

        def getter_client(row):
            if 'client' in row and row.client is not None:
                client = row.client
                if isinstance(client, Dict):
                    if 'business_name' in client:
                        return client.business_name
                    elif 'name' in client:
                        return client.name
                    elif 'rfc' in client:
                        return client.rfc
                    elif 'id' in client:
                        return client.id
                elif isinstance(client, str):
                    return client

        table.columns['datetime'].getter_data = ['datetime', 'date']
        table.columns['client'].getter_data = getter_client
        table.columns['amount'].getter_data = ['amount', 'total']

        table.datasource = result
        e['table'] = table
        e['list'] = result


class Item(dict):
    @property
    def price_value(self):
        if 'price' in self:
            price = self.price
            if 'value' in price:
                return price.value


class Model_Items(Table):
    def __init__(self):
        Table.__init__(self, 'items')
        self.columns.add('sku', str)
        self.columns.add('quanty', Decimal, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('price', Decimal, 'c')
        self.columns.add('amount', Decimal, 'c')
        self.readonly = True

        def getter_price_data(row):
            if 'price' in row:
                price = row.price
                if isinstance(price, (Decimal, int)):
                    return price
                elif isinstance(price, Dict) and 'value' in price:
                    return price.value

        def getter_amount_data(row):
            price = getter_price_data(row)
            if price is not None and 'quanty' in row:
                return round(price * row.quanty, 2)

        self.columns['price'].getter_data = getter_price_data
        self.columns['amount'].getter_data = getter_amount_data
        self.datasource = list()

    def totalamount(self):
        total = Decimal()
        if self.datasource is not None:
            for item in self.datasource:
                amount = self.columns['amount'].getter_data(item)
                if amount is not None:
                    total += amount
        return round(total, 2)

    remove_item = Table.remove_row


class Table_View_Items(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)


class Processer_Command(Line_Edit):
    def __init__(self, parent=None):
        Line_Edit.__init__(self, parent)
        self.handler_command = None
        self.command = Event()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.command(self.text)
            self.text = None
        elif event.key() == Qt.Key_Escape:
            self.setText('')
        Line_Edit.keyPressEvent(self, event)


class Select_Payway(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.setWindowTitle(self.__class__.__name__)
        self.resize(280, 90)
        btn_cash = Push_Button('cash (F6)', self)
        btn_close = Push_Button('close (Escape)', self)

        layoutmain = V_Box_Layout(self)
        layoutmain.addWidget(btn_cash)
        layoutmain.addWidget(btn_close)
        self.layout = layoutmain
        self.selected = None
        btn_cash.clicked.connect(self.chose_cash)
        btn_close.clicked.connect(self.chose_close)

    def chose_cash(self):
        self.selected = 'cash'
        self.close()

    def chose_close(self):
        self.selected = None
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F6:
            self.chose_cash()
        elif event.key() in [Qt.Key_Escape]:
            self.chose_close()
        else:
            Dialog.keyPressEvent(self, event)


class Prusia(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.agent_portia = Client('', 'portia')
        self.resize(700, 680)
        self.setWindowTitle('Prusia')
        self.cwidget = Widget(self)

        self.widgetclient = Widget_Client(self.cwidget)
        self.widgetclient.name_editable = True

        lbl_amount = Label('amount: ', self.cwidget)

        self.lbl_amount = Label(self.cwidget)

        font_amount = QFont()
        font_amount.setPointSize(20)
        lbl_amount.setFont(font_amount)
        self.lbl_amount.setFont(font_amount)
        lbl_amount.fix_size_based_on_font()

        self.tableview = Table_View_Items(self.cwidget)

        self.txt_command = Processer_Command(self.cwidget)

        layouttop = H_Box_Layout()
        layouttop.addStretch()
        layouttop.addWidget(lbl_amount)
        layouttop.addWidget(self.lbl_amount)

        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addItem(layouttop)
        layoutmain.addWidget(self.widgetclient)

        layoutmain.addWidget(self.tableview)
        layoutmain.addWidget(self.txt_command)

        self.cwidget.setLayout(layoutmain)

        self.modelitems = Model_Items()
        self.tableview.model = self.modelitems

        def update_amount(*args):
            self.lbl_amount.text = format_currency(self.modelitems.totalamount())

        self.modelitems.any_change_in_datasource.suscribe(update_amount)
        self.txt_command.command.suscribe(self.process_command)

        def handler(event):
            if isinstance(event, QKeyEvent) and event.key() in [Qt.Key_Up, Qt.Key_Down]:
                print(event.key())
                current_index = self.tableview.currentIndex()
                if event.key() == Qt.Key_Up:
                    if current_index.isValid() and current_index.row() > 0:
                        self.tableview.selectRow(current_index.row() - 1)
                    elif len(self.items):
                        self.tableview.selectRow(len(self.items) - 1)
                elif event.key() == Qt.Key_Down:
                    if current_index.isValid() and current_index.row() < len(self.items) - 1:
                        self.tableview.selectRow(current_index.row() + 1)
                    elif len(self.items):
                        self.tableview.selectRow(0)

        self.txt_command.key_down.suscribe(handler)

        update_amount()

        self.searcher_item = None

        self.agent_serena = Client(self.APP_ID, 'serena')
        self.agent_perla = Client('Prusia', 'perla')
        self.agent_vasya = Client('Prusia', 'vasya')
        self.agent_caroline = Client('Prusia', 'caroline')
        self.txt_command.installEventFilter(self)
        self.tableview.installEventFilter(self)
        self.widgetclient.installEventFilter(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if not self.txt_command.hasFocus():
                self.txt_command.setFocus()

        elif event.key() == Qt.Key_F2:
            dialog = Select_Sale_Local_Saved(self)
            dialog.exec_()
            if dialog.selected is not None:
                self.save_sale_in_local()
                sale = dialog.selected
                self.items = sale['items']
                if 'client' in sale:
                    self.client = sale.client
                else:
                    self.client = Dict()
                # self.sale = dialog.selected
        elif event.key() == Qt.Key_F3:
            self.save_sale_in_local()
            self.clear_sale()
            pass
        elif event.key() == Qt.Key_F6:
            if len(self.modelitems.datasource) > 0:
                switch = Select_Payway(self)
                switch.exec_()
                if switch.selected is not None and switch.selected == 'cash':
                    self.close_sale_cash()
        elif event.modifiers() & Qt.AltModifier and event.key() == Qt.Key_I and False:
            ticket = Dict({'type': 'serena/ticket', 'datetime': datetime_isoformat(datetime.now()),
                           'items': deepcopy(self.items)})
            for item in ticket.items[:]:
                if 'sku' not in item or 'description' not in item or 'price' not in item:
                    ticket.remove(item)
        elif event.key() == Qt.Key_F9:
            r = Message_Box.question(self, 'Cancelar', 'Quieres cancelar la venta?', Message_Box.Yes | Message_Box.No, Message_Box.No)
            if r == Message_Box.Yes:
                self.clear_sale()

        Main_Window.keyPressEvent(self, event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_I and event.modifiers() == Qt.AltModifier:
                items = deepcopy(self.modelitems.datasource)
                for item in items:
                    if 'price' in item:
                        price = item.price
                        if isinstance(price, (dict, Dict)) and 'value' in price:
                            item.price = price.value
                        elif isinstance(price, (Decimal, int)):
                            item.price = price
                    if 'price' in item and 'quanty' in item:
                        item.amount = item.price * item.quanty
                ticket = Dict({'items': items, 'amount': self.modelitems.totalamount(),
                               'type': 'serena/ticket', 'folio': 'print',
                               'datetime': datetime_isoformat(datetime.now()),
                               'authenticity': 'print'})
                from portia.remote import print_document
                print_document(ticket)
                return True
        return False

    def save_sale_in_local(self):
        items = deepcopy(self.items)
        for item in items[:]:
            if 'sku' not in item or 'description' not in item or 'quanty' not in item or 'price' not in item:
                items.remove(item)
        if not len(items) > 0:
            return
        sale = Dict({'client': self.client, 'items': items, 'datetime': datetime_isoformat(datetime.now()),
                     'amount': self.modelitems.totalamount()})
        dictutils.dec_to_float(sale)
        coll_sales_saved.insert_one(sale)

    def clear_sale(self):
        self.items = list()
        client = self.client
        if client is not None and 'wholesale' in client:
            new_client = Dict({'wholesale': client.wholesale})
            self.client = new_client
        else:
            self.client = Dict()

    @property
    def client(self):
        return self.widgetclient.client

    @client.setter
    def client(self, x):
        self.widgetclient.client = x

    @property
    def items(self):
        return self.modelitems.datasource

    @items.setter
    def items(self, x):
        self.modelitems.datasource = x

    def process_command(self, cmd):
        if cmd is None or not cmd:
            return
        index = self.tableview.currentIndex()
        from utils import isnumeric
        if not index.isValid():
            if cmd == '--':
                return
            elif cmd == '++':
                return
            elif cmd[0] == '+' and isnumeric(cmd[1:]):
                return
            elif cmd[0] == '-' and isnumeric(cmd[1:]):
                return
            elif cmd[0] == '*' and isnumeric(cmd[1:]):
                return
            else:
                self.handle_process_command_search_text(cmd)
                return

        item = self.items[index.row()]

        if cmd == '--':
            self.modelitems.remove_row(index.row())
            return
        elif cmd == '++':
            item.quanty = item.quanty + 1 if 'quanty' in item else 1
        elif cmd[0] == '+' and isnumeric(cmd[1:]):
            item.quanty = item.quanty + Decimal(cmd[1:]) if 'quanty' in item else Decimal(cmd[1:])
        elif cmd[0] == '-' and isnumeric(cmd[1:]):
            if 'quanty' in item:
                item.quanty -= Decimal(cmd[1:])
        elif cmd[0] == '*' and isnumeric(cmd[1:]):
            item.quanty = Decimal(cmd[1:])
        else:
            self.handle_process_command_search_text(cmd)
            return

        if 'quanty' not in item or item['quanty'] <= Decimal():
            self.modelitems.remove_item(index.row())
        else:
            self.modelitems.notify_row_changed(index.row())

    def handle_process_command_search_text(self, txt):
        for item in self.items:
            if 'selected_with' in item and item['selected_with'] == txt:
                item.quanty = item.quanty + 1 if 'quanty' in item else 1
                index = self.items.index(item)
                self.tableview.selectRow(index)
                self.modelitems.notify_row_changed(index)
                return
        if self.searcher_item is None:
            self.searcher_item = Search_Product(self)
            self.searcher_item.store = {'id': '42-3'}
        searcher = self.searcher_item
        result = searcher.search(txt)

        if result is not None:
            if 'sku' in result:
                for item in self.items:
                    if 'sku' in item and item.sku == result.sku:
                        item.quanty = item.quanty + 1 if 'quanty' in item else 1
                        index = self.items.index(item)
                        self.tableview.selectRow(index)
                        self.modelitems.notify_row_changed(index)
                        return
                else:
                    result.price = self.get_price(result['sku'])
                    price = result.price
                    if isinstance(price, Dict) and 'type' in price and price.type == 'perla/scale_prices':
                        pass
                    result.quanty = 1
                    self.modelitems.add_row(result)
                    self.tableview.selectRow(self.items.index(result))

    def get_price(self, sku):
        msg = {'type_message': 'find_one', 'type': 'perla/price', 'query': {'sku': sku}}
        client = self.client
        if client is not None and isinstance(client, dict) and 'wholesale' in client:
            msg['query']['wholesale'] = client['wholesale']
        answer = self.agent_perla(msg)
        if 'result' in answer and answer['result'] is not None:
            price = answer.result
            if isinstance(price, Dict) and 'type' in price and price.type == 'perla/scale_prices':
                scale_prices = price
                for price in scale_prices.prices:
                    if 'minimum' not in price:
                        price.minimum = 0
                minimum_count = list()
                for price in scale_prices.prices:
                    minimum = find_one(lambda x: x.minimum == price.minimum, minimum_count)
                    if minimum is not None:
                        minimum.count += 1
                    else:
                        minimum = Dict({'minimum': price.minimum, 'count': 1})
                        minimum_count.append(minimum)
                if len([minimum for minimum in minimum_count if minimum.count > 1]) > 0:
                    raise Exception('scale_prices just should contains 1 base count')

                scale_prices.prices.sort(key=lambda x: x.minimum)
                price = scale_prices.prices[0]
                for _price in scale_prices.prices[1:]:
                    if _price.minimum <= 1:
                        price = _price
                    else:
                        break
                if isinstance(price, (Decimal, int)):
                    scale_prices.value = price
                elif isinstance(price, Dict) and 'value' in price:
                    scale_prices.value = price.value
                price = scale_prices
            return price
        else:
            return None

    APP_ID = '31-10'

    def close_sale_cash(self):
        msg = Dict({'type_message': 'action', 'action': 'vasya/begin_transaction', 'transaction': {}})

        no_vasya_tx = False
        if hasattr(self, 'box') and self.box is not None:
            msg.transaction.account = self.box
        elif hasattr(self, 'cash_drawer') and self.cash_drawer is not None:
            msg.transaction.account = self.cash_drawer
        elif hasattr(self, 'cash_register') and self.cash_register is not None:
            msg.transaction.account = self.cash_register
        else:
            no_vasya_tx = True

        if not no_vasya_tx:
            account = deepcopy(msg.transaction.account)

            for k in list(account.keys()):
                if k not in ['id', 'type']:
                    del account[k]
            msg.transaction.account = account
            answer = self.agent_vasya(msg)
            tx = answer.transaction
        else:
            tx = None

        msg = Dict({'type_message': 'action', 'action': 'serena/close_sale', 'v': 2, 'make_inventory_movement': True,
                    'document_sale_required': 'serena/ticket'})

        sale = Dict({'amount': self.modelitems.totalamount(), 'items': deepcopy(self.modelitems.datasource),
                     'datetime': datetime_isoformat(datetime.now())})

        for item in sale['items'][:]:
            if 'sku' not in item or 'quanty' not in item:
                sale['items'].remove(item)

        for item in sale['items']:
            if 'price' not in item and (isinstance(item.price, (D, int, float)) or isinstance(item.price, dict) and 'value' in item.price):
                Message_Box.warning(self, 'Error', 'Es necesario que todos los articulos cotengan precio')
                return

        client = self.client
        if client is not None and 'name' in client:
            sale.client = deepcopy(client)
            client = sale.client
            for k in list(client.keys()):
                if k not in ['id', 'type', 'name', 'rfc', 'business_name']:
                    del client[k]
            if 'business_name' in client and 'name' in client:
                del client.business_name
        else:
            sale.client = {}
        msg.sale = sale
        answer = self.agent_serena(msg)
        if 'document' in answer:
            doc = answer.document
            if tx is not None:
                tx.document = {'id': doc.id, 'type': doc.type}
                if 'amont' in doc:
                    tx.document.value = doc.amount
                self.agent_serena({'type_message': 'action', 'action': 'serena/set_payment', 'document': doc,
                                   'payment': {'id': tx.id, 'type': tx.type, 'value': tx.value}})

                self.agent_vasya({'type_message': 'action', 'action': 'vasya/commit_transaction', 'transaction': tx})
            from portia.remote import print_document
            print_document(answer.document)
        self.clear_sale()


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Prusia()
    vv.show()
    sys.exit(app.exec_())
