from isodate import datetime_isoformat
from datetime import datetime
from isis.utils import format_number, format_currency
from decimal import Decimal as D
from isis.data_model.table import Table
from isis.main_window import Main_Window
from isis.widget import Widget
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.grid_layout import Grid_Layout
from isis.table_view import Table_View
from isis.v_box_layout import V_Box_Layout
from dict import Dict as dict, List as list
from sarah.acp_bson import Client
from perla.prices import get_last_purchase_price
from itzamara.remote import find_one_item, get_item_mass
from valentine.remote import get_inventory_absolut
from isis.itzamara.search_item import Search_Item
from isis.message_box import Message_Box
from copy import deepcopy


agent_itzamara = Client('', 'itzamara')
agent_valentine = Client('', 'valentine')

answer = agent_itzamara({'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/units_mass'})
if 'result' in answer and answer['result'] is not None:
    repository_units_mass = answer['result']
else:
    raise Exception('itzamara does not knos the units mass')


def search_unit(symbol):
    if symbol is not None:
        for unit in repository_units_mass:
            if unit.symbol == symbol:
                return unit


class Items_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.enable_delete_row_with_supr = True
        self.title_question_delete_row = 'Suprimir Articulo'
        self.text_question_delete_row = 'Deseas Suprimir El Articulo Seleccionado??'


class Items_Table(Table):
    def __init__(self):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('quanty', D, '#,##0.###')
        self.columns.add('description', str)
        self.columns.add('mass', str)
        self.columns.add('mass_net', str)
        self.columns.add('value', D, 'c')
        self.columns.add('from_inventory_initial', D, '#,##0.###')
        self.columns.add('to_inventory_initial', D, '#,##0.###')
        self.columns.add('from_inventory_final', D, '#,##0.###')
        self.columns.add('to_inventory_final', D, '#,##0.###')

        self.with_new_empty_row = True

        for n in ['mass', 'mass_net', 'value', 'from_inventory_initial', 'to_inventory_initial',
                  'from_inventory_final', 'to_inventory_final']:
            self.columns[n].readonly = True

        self.columns['sku'].changing_item_value = self.changing_item_value_sku
        self.columns['description'].changing_item_value = self.changing_item_value_description
        self.columns['value'].getter_data = lambda x: x.quanty * x.value if 'quanty' in x and 'value' in x else None
        self.columns['mass'].getter_data = self.getter_data_mass
        self.columns['mass_net'].getter_data = self.getter_data_mass_net
        self.columns['from_inventory_final'].getter_data = self.getter_data_from_inventory_final
        self.columns['to_inventory_final'].getter_data = self.getter_data_to_inventory_final

        self.datasource = list()
        self.storage_from = None
        self.storage_to = None

    @staticmethod
    def getter_data_mass(row):
        if 'mass' in row:
            mass = row.mass
            return format_number(mass.n) + ' ' + mass.unit

    @staticmethod
    def getter_data_mass_net(row):
        if 'mass' in row and 'quanty' in row:
            mass = row.mass
            return format_number(mass.n * row.quanty) + ' ' + mass.unit

    @staticmethod
    def getter_data_from_inventory_final(row):
        if 'from_inventory_initial' in row:
            inventory = row.from_inventory_initial
            if 'quanty' in row:
                inventory -= row.quanty
            return inventory

    @staticmethod
    def getter_data_to_inventory_final(row):
        if 'to_inventory_initial' in row:
            inventory = row.to_inventory_initial
            if 'quanty' in row:
                inventory += row.quanty
            return inventory

    def set_storage_from(self, value):
        self.storage_from = value

    def set_storage_to(self, value):
        self.storage_to = value

    def changing_item_value_sku(self, item, value):
        if value is not None and value:
            if 'sku' in item and item.sku == value:
                return False
            item_found = find_one_item(sku=value)
            if item_found is not None:
                self.set_item(item, item_found)
        elif 'sku' in item:
            self.clear_item(item)
        else:
            return False

    def changing_item_value_description(self, item, value):
        if value is not None and value:
            if 'description' in item and item.description == value:
                return False
            searcher = Search_Item()
            result = searcher.search(value)
            if result is not None:
                self.set_item(item, result)
            else:
                self.clear_item(item)
        elif 'description' in item:
            self.clear_item(item)
        else:
            return False

    @staticmethod
    def clear_item(item):
        kk = ['sku', 'description', 'type', 'value', 'mass', 'from_inventory_initial', 'to_inventory_initial']
        for k in kk:
            if k in item:
                del item[k]

    def set_item(self, item, to_set):
        item.sku = to_set.sku
        item.description = to_set.description
        if 'type' in to_set:
            item.type = to_set.type
        elif 'type' in item:
            del item.type
        mass = get_item_mass(item)
        if mass is not None:
            item.mass = mass
        elif 'mass' in item:
            del item.mass

        if self.storage_from is not None:
            answer = get_inventory_absolut(item, self.storage_from)
            item.from_inventory_initial = answer.inventory_absolut
        elif 'from_invenrory_initial' in item:
            del item.from_inventory_initial
        if self.storage_to is not None:
            answer = get_inventory_absolut(item, self.storage_to)
            item.to_inventory_initial = answer.inventory_absolut
        elif 'to_inventory_initial' in item:
            del item.to_inventory_initial

        price = get_last_purchase_price(item)
        if price is not None:
            item.value = price
        elif 'value' in item:
            del item.value

    def totalvalue(self):
        value = D()
        for item in self.datasource:
            if 'quanty' in item and 'value' in item:
                value += round(item.quanty * item.value, 2)
        return value

    def totalmass(self, unit):
        totalmass = dict({'unit': unit})
        grams = D()
        for item in self.datasource:
            if 'quanty' in item and 'mass' in item:
                item_mass = item.mass
                unit = search_unit(item_mass.unit)
                if unit is None:
                    raise Exception('unit %s is not in repository' % item_mass['unit'])
                grams += item.quanty * item_mass.n * unit.multiple_gram
        unit = search_unit(totalmass.unit)
        totalmass.n = grams / unit.multiple_gram
        return totalmass


class Create_Transfer(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Crear Transferencia de Mercancias. valentine/transfer')
        self.resize(1200, 700)

        cwidget = Widget()
        self.central_widget = cwidget
        self.widget_storage_from = Widget_Viewer_Storage(cwidget)
        self.widget_storage_to = Widget_Viewer_Storage(cwidget)
        self.widget_storage_from.with_button_change = True
        self.widget_storage_to.with_button_change = True
        self.widget_storage_from.label = 'Desde'
        self.widget_storage_to.label = 'Hacia'
        lbl_datetime = Label('datetime: ', cwidget)
        lbl_mass = Label('mass: ', cwidget)
        lbl_value = Label('value: ', cwidget)

        lbl_datetime.fix_size_based_on_font()
        lbl_mass.fix_size_based_on_font()
        lbl_value.fix_size_based_on_font()

        self.txt_datetime = Line_Edit(cwidget)
        self.lbl_mass = Label(cwidget)
        self.lbl_value = Label(cwidget)

        self.txt_datetime.setFixedWidth(200)

        self.tableview = Items_Table_View(cwidget)
        # from PySide2.QtWidgets import QSpacerItem
        layoutmain = V_Box_Layout(cwidget)
        headlayout = Grid_Layout()
        # headlayout.addItem(QSpacerItem(0, 0))
        headlayout.addWidget(lbl_mass, 0, 0)
        headlayout.addWidget(self.lbl_mass, 0, 1)
        headlayout.addWidget(lbl_value, 0, 2)
        headlayout.addWidget(self.lbl_value, 0, 3)
        headlayout.addWidget(lbl_datetime, 0, 4)
        headlayout.addWidget(self.txt_datetime, 0, 5, 1, 1)

        layoutmain.addLayout(headlayout)
        layoutmain.addWidget(self.widget_storage_from)
        layoutmain.addWidget(self.widget_storage_to)
        layoutmain.addWidget(self.tableview)

        cwidget.layout = layoutmain

        self.itemstable = Items_Table()
        self.tableview.model = self.itemstable

        self.widget_storage_from.storage_changed.suscribe(self.itemstable.set_storage_from)
        self.widget_storage_to.storage_changed.suscribe(self.itemstable.set_storage_to)
        self.itemstable.any_change_in_datasource.suscribe(self.update_mass)
        self.itemstable.any_change_in_datasource.suscribe(self.update_value)
        # from valentine.remote import find_one_storage
        # self.widget_storage_from.storage = find_one_storage('57-6')
        # self.widget_storage_to.storage = find_one_storage('42-3')
        self.update_value()
        self.update_mass()

        toolbar = self.addToolBar('File')
        create_action = toolbar.addAction('Crear Transferencia')
        create_transfer_order = toolbar.addAction('Crear Orden de Transferencia valentine/transfer_order')
        create_action.triggered.connect(self.create)
        create_transfer_order.triggered.connect(self.create_transfer_order)

    def get_transfer_abstract(self):
        transfer = dict()
        if self.txt_datetime.text is not None and self.txt_datetime.text:
            transfer.datetime = self.txt_datetime.text
        else:
            transfer.datetime = datetime_isoformat(datetime.now())

        if self.widget_storage_from.storage is not None:
            transfer['from'] = deepcopy(self.widget_storage_from.storage)
        else:
            Message_Box.warning(self, 'error', 'valentine/transfer debe tener un almacen origen ')
            return

        if self.widget_storage_to.storage is None:
            Message_Box.warning(self, 'error', 'valentine/tranfer debe tener un almacen destino')
            return
        else:
            if self.widget_storage_to.storage.id == transfer['from'].id:
                Message_Box.warning(self, 'error', 'Los almacenes no deben de ser los mismos')
                return
            else:
                transfer['to'] = deepcopy(self.widget_storage_to.storage)

        items = deepcopy(self.itemstable.datasource)
        transfer.mass = self.itemstable.totalmass('kg')
        transfer.value = self.itemstable.totalvalue()

        for item in items:
            if 'quanty' not in item:
                Message_Box.warning(self, 'error', 'todos los articulos deben tener cantidad')
                return

            if 'sku' not in item:
                Message_Box.warning(self, 'error', 'todos los articulos deben tener sku')
                return

            for k in list(item.keys()):
                if k not in ['value', 'sku', 'description', 'mass', 'quanty', 'type']:
                    del item[k]

        transfer['items'] = items
        return transfer

    def create(self):
        transfer = self.get_transfer_abstract()
        transfer.type = 'valentine/transfer'
        msg = dict({'type_message': 'action', 'action': 'valentine/create_transfer', 'transfer': transfer})
        answer = agent_valentine(msg)
        if 'error' in answer:
            Message_Box.warning(self, 'error', 'un error ah ocurrido al crear valentine/transfer')
            return
        else:
            Message_Box.information(self, 'Creada', 'valentine/transfer ah sido creada exitosamente')
            self.close()

    def create_transfer_order(self):
        order = self.get_transfer_abstract()
        order.type = 'valentine/transfer_order'

    def update_value(self, *args):
        self.lbl_value.text = format_currency(self.itemstable.totalvalue())

    def update_mass(self, *args):
        mass = self.itemstable.totalmass('kg')
        from isis.utils import format_number
        self.lbl_mass.text = format_number(mass.n) + ' ' + mass.unit


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    mw = Create_Transfer()
    mw.show()
    sys.exit(app.exec_())
