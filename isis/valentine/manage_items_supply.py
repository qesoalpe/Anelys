from isis.data_model.table import Table
from isis.main_window import Main_Window
from isis.widget import Widget as Widget_cls
from decimal import Decimal as D
from isis.table_view import Table_View
from PySide2.QtCore import QSortFilterProxyModel
import re
from isis.v_box_layout import V_Box_Layout
from katherine import d1, d6
from itzamara import key_to_sort_item
from isis.label import Label
from isis.line_edit import Line_Edit
from isis.h_box_layout import H_Box_Layout
from dict import Dict as dict, List as list
from isodate import parse_duration, duration_isoformat
from isodate.duration import Duration
from datetime import timedelta
from isis.message_box import Message_Box
from PySide2.QtGui import QValidator
from isis.check_box import Check_Box
from sarah.acp_bson import Client
pp = 22


agent_valentine = Client('', 'valentine')

answer = agent_valentine({'type_message': 'find', 'type': 'valentine/storage', 'query': {}})

storages = answer.result

regexp_duration = re.compile(r'^P\d+D$')


class Validator_Iso8601(QValidator):
    def validate(self, input, pos):
        return QValidator.Invalid if regexp_duration.match(input) is None else QValidator.Acceptable


validator_duration_iso8601 = Validator_Iso8601()


demand_maximum_default = parse_duration('P30D')
demand_reoder_point_default = parse_duration('P15D')


class Items_Model(Table):
    def __init__(self):
        Table.__init__(self)
        columns = self.columns
        columns.add('sku', str)
        columns.add('description', str)
        columns.add('method', str)
        columns.add('other_storage', D, '#,##0.###')
        columns.add('for_arrive', D, '#,##0.###')
        columns.add('inventory', D, '#,##0.###')
        columns.add('demand', str)
        columns.add('maximum', D, '#,##0.###')
        columns.add('reorder_point', D, '#,##0.###')
        columns.add('covered', str)
        columns.add('demand_reorder_point', str)
        columns.add('demand_maximum', str)
        columns.add('supply_suggested', D, '#,##0.###')
        columns['inventory'].getter_data = ['inventory_absolut', 'inventory']
        columns['covered'].getter_data = ['covered_error_str', 'covered_str', 'covered']
        columns['demand'].getter_data = self.demand_getter_data
        columns['demand_maximum'].read_only = False
        self.readonly = True
        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage

    def set_storage(self, storage):
        self.storage = storage

    @staticmethod
    def demand_getter_data(item):
        from isis.utils import format_number
        if 'demand' in item:
            demand = item.demand
            if 'n' in demand and 'period_str' in demand and isinstance(demand.period_str, str):
                return demand.period_str + '/' + format_number(demand.n)
            elif 'n' in demand and 'period' in demand and isinstance(demand.period, str):
                return demand.period + '/' + format_number(demand.n)
            elif 'n' in demand and 'period' in demand and isinstance(demand.period, (timedelta, Duration)):
                return duration_isoformat(demand.period) + '/' + format_number(demand.n)
            elif 'n' in demand:
                return format_number(demand.n)

    def getter_data_covered(self, row):
        if 'demand' in row and 'inventory' in row:
            pass


class Items_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)


class Sort_Filter_Proxy_Model_Items(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self)
        self._regex = None
        self.items = None
        self.txt_search = ''

    @property
    def regex(self):
        return self._regex

    @regex.setter
    def regex(self, regex):
        if regex is not None:
            import re
            self._regex = re.compile(regex)
        else:
            self._regex = None

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if self.items is not None:
            if self.regex is not None:
                item = self.items[sourceRow]
                return len(self.regex.findall(item.description)) > 0
            else:
                return True
        else:
            return True

    def lessThan(self, left, right):
        col_inventory = self.sourceModel().columns['inventory']
        col_description = self.sourceModel().columns['description']
        col_covered = self.sourceModel().columns['covered']
        col_demand = self.sourceModel().columns['demand']
        i = left.column()

        if i == col_inventory.index:
            left = self.items[left.row()]
            right = self.items[right.row()]
            left = col_inventory.get_data(left)
            right = col_inventory.get_data(right)
            if left is not None and right is not None:
                return left < right
            return False
        elif i == col_description.index:
            left = self.items[left.row()]
            right = self.items[right.row()]
            return key_to_sort_item(left) < key_to_sort_item(right)
        elif i == col_covered.index:
            left = self.items[left.row()]
            right = self.items[right.row()]
            left = left.covered.total_seconds() if 'covered' in left else 0
            right = right.covered.total_seconds() if 'covered' in right else 0
            return left < right
        elif i == col_demand.index:
            left = self.items[left.row()]
            right = self.items[right.row()]
            left = left.demand.comparable if 'demand' in left else 0
            right = right.demand.comparable if 'demand' in right else 0
            return left < right
        else:
            return QSortFilterProxyModel.lessThan(self, left, right)

    def setSourceModel(self, model):
        QSortFilterProxyModel.setSourceModel(self, model)
        self.items = model.datasource

        def any(*args):
            self.items = self.sourceModel().datasource

        self.sourceModel().modelReset.connect(any)

    # def flags(self, *args, **kwargs):
    #     return self.sourceModel().flags(*args, **kwargs)


class Widget(Widget_cls):
    def __init__(self, *args, **kwargs):
        Widget_cls.__init__(self, *args, **kwargs)

        self._demand_maximum_str = None
        self._demand_reorder_point_str = None
        self._demand_maximum = None  # parse_duration(self.demand_to_cover_str)
        self._demand_reorder_point = None  # parse_duration(self.demand_reorder_point_str)
        from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage

        self.layout = V_Box_Layout()
        lbl_search = Label('search: ', self)
        self.txt_search_text = Line_Edit(self)

        self.widget_storage = Widget_Viewer_Storage(self)
        self.widget_storage.with_button_change = True

        lbl_demand_maximum = Label('Demanda Maxima: ', self)
        self.txt_demand_maximum = Line_Edit(self)

        lbl_demand_reorder_point = Label('demand_reorder_point: ', self)
        self.txt_demand_reorder_point = Line_Edit(self)

        lbl_demand_maximum.fix_size_based_on_font()
        lbl_demand_reorder_point.fix_size_based_on_font()

        self.chk_filters = Check_Box('Filters', self)

        # self.txt_demand_reorder_point.setValidator(validator_duration_iso8601)
        # self.txt_demand_maximum.setValidator(validator_duration_iso8601)

        self.tableview = Items_View(self)
        layout = H_Box_Layout()
        layout.addWidget(lbl_search)
        layout.addWidget(self.txt_search_text)
        self.layout.addLayout(layout)
        self.layout.addWidget(self.widget_storage)
        layout = H_Box_Layout()
        layout.addWidget(lbl_demand_reorder_point)
        layout.addWidget(self.txt_demand_reorder_point)
        layout.addWidget(lbl_demand_maximum)
        layout.addWidget(self.txt_demand_maximum)
        layout.addWidget(self.chk_filters)
        self.layout.addLayout(layout)
        self.layout.addWidget(self.tableview)

        self.model = Items_Model()
        self.modelproxy = Sort_Filter_Proxy_Model_Items()
        self.modelproxy.setSourceModel(self.model)

        self.tableview.model = self.modelproxy
        self.tableview.setSortingEnabled(True)

        def hh(*args):
            # if event.key() in [Qt.Key_Enter, Qt.Key_Return] or True:
            txt = self.txt_search_text.text
            if txt != self.modelproxy.txt_search:
                r = re.compile('.*' + re.escape(txt).replace('\\ ', '.*') + '.*', re.I)
                self.modelproxy.regex = r
                self.modelproxy.modelReset.emit()
                self.modelproxy.txt_search = txt

        # self.txt_search_text.timeoutdelayediting = 500
        self.txt_search_text.editingFinished.connect(hh)
        self.txt_demand_reorder_point.editingFinished.connect(self.handle_demand_reorder_point_editing_finished)
        self.txt_demand_maximum.editingFinished.connect(self.handle_demand_maximum_editing_finished)

        # self.txt_period_to_cover.text_edited.suscribe(self.handle_txt_period_to_cover_text_edited)
        self.widget_storage.storage_changed.suscribe(self.model.set_storage)

        self._mis = None
        self._storage = None
        self.demand_maximum = demand_maximum_default
        self.demand_reorder_point = demand_reoder_point_default

    def handle_demand_reorder_point_editing_finished(self):
        if regexp_duration.match(self.txt_demand_reorder_point.text) is None:
            self.txt_demand_reorder_point.text = self._demand_reorder_point_str
            return
        self.demand_reorder_point = parse_duration(self.txt_demand_reorder_point.text)

    def handle_demand_maximum_editing_finished(self):
        if regexp_duration.match(self.txt_demand_maximum.text) is None:
            self.txt_demand_maximum.text = self._demand_maximum_str
            return
        self.demand_maximum = parse_duration(self.txt_demand_maximum.text)

    @property
    def manage_items_supply(self):
        return self._mis

    @property
    def demand_maximum(self):
        return self._demand_maximum

    @demand_maximum.setter
    def demand_maximum(self, demand_maximum):
        if isinstance(demand_maximum, str):
            demand_maximum = parse_duration(demand_maximum)
        if demand_maximum is None:
            self._demand_maximum_str = None
            self._demand_maximum = None
            if self.txt_demand_maximum.text:
                self.txt_demand_maximum.text = None
        else:
            self._demand_maximum = demand_maximum
            self._demand_maximum_str = duration_isoformat(demand_maximum)
            if not self.txt_demand_maximum.text or self.txt_demand_maximum.text != self._demand_maximum_str:
                self.txt_demand_maximum.text = self._demand_maximum_str
            if self.manage_items_supply is not None:
                for item in self.manage_items_supply['items']:
                    supply_suggested = self.get_supply_suggested(item)
                    if supply_suggested is not None:
                        item.supply_suggested = supply_suggested
                    elif 'supply_suggested' in item:
                        del item.supply_suggested
                self.model.modelReset.emit()

    @property
    def demand_reorder_point(self):
        return self._demand_reorder_point

    @demand_reorder_point.setter
    def demand_reorder_point(self, demand_reoder_point):
        if isinstance(demand_reoder_point, str):
            demand_reoder_point = parse_duration(demand_reoder_point)
        if demand_reoder_point is None:
            self._demand_reorder_point_str = None
            self._demand_reorder_point = None
            if self.txt_demand_reorder_point.text:
                self.txt_demand_reorder_point.text = None
        else:
            self._demand_reorder_point_str = duration_isoformat(demand_reoder_point)
            self._demand_reorder_point = demand_reoder_point
            if not self.txt_demand_reorder_point.text or self.txt_demand_reorder_point.text != self._demand_reorder_point_str:
                self.txt_demand_reorder_point.text = self._demand_reorder_point_str
            if self.manage_items_supply is not None:
                for item in self.manage_items_supply['items']:
                    supply_suggested = self.get_supply_suggested(item)
                    if supply_suggested is not None:
                        item.supply_suggested = supply_suggested
                    elif 'supply_suggested' in item:
                        del item.supply_suggested
                self.model.modelReset.emit()

    @manage_items_supply.setter
    def manage_items_supply(self, mis):
        if mis is not None:

            if isinstance(mis, str):
                mis = d1.valentine.manage_items_supply.find_one({'id': '226-1'}, {'_id': False})
            # from piper.remote import get_provider_sells
            # provider_sells_sku = [item.sku for item in get_provider_sells('61-10')]
            #
            # mis['items'] = [item for item in mis['items'] if item.sku in provider_sells_sku]
            d6.ping(True)
            d6_cursor = d6.cursor()
            from valentine.remote import get_inventory_absolut as get_inventory
            mis['items'] = get_inventory(mis['items'])
            mis['items'].sort(key=key_to_sort_item)
            self._mis = mis

            storage = mis.storage
            for item in mis['items']:
                if 'inventory_absolut' in item:
                    item.inventory = item.inventory_absolut
                    del item.inventory_absolut
                r = d6_cursor.execute('select demand, period from valentine.item_demand '
                                      'where storage_id = %s and item_sku = %s limit 1;',
                                      (storage.id, item.sku))
                if r == 1:
                    demand, period = d6_cursor.fetchone()
                    item.demand = dict({'n': demand, 'period': parse_duration(period), 'period_str': period})

                    total_seconds = item.demand.period.total_seconds()

                    if item.demand.n != 0 and total_seconds != 0:
                        item.demand.comparable = item.demand.n / D(total_seconds)
                    else:
                        item.demand.comparable = 0

                    if item.inventory != D() and item.demand.n == D():
                        item.covered_error_str = 'demanda nula'
                    elif item.inventory == D() and item.demand.n > D():
                        item.covered = parse_duration('P0D')
                        item.covered_str = 'P0D'
                    elif item.inventory == D() and item.demand.n <= D():
                        item.covered_error_str = 'inventario insuficiente & demanda nula'
                    else:
                        item.covered = item.demand.period * round(float(item.inventory / item.demand.n), 3)
                        item.covered_str = duration_isoformat(item.covered)

                r = d6_cursor.execute('select maximum, reorder_point, method, demand_maximum, demand_reorder_point '
                                      'from valentine.method_evaluation_supply '
                                      'where storage_id = %s and item_sku = %s limit 1;',
                                      (storage.id, item.sku))
                if r == 1:
                    maximum, reorder_point, method, demand_maximum, demand_reorder_point = d6_cursor.fetchone()
                    if maximum is not None:
                        item.maximum = maximum

                    if reorder_point is not None:
                        item.reorder_point = reorder_point
                    if method is not None:
                        item.method = method

                    if demand_maximum is not None or demand_reorder_point is not None:
                        if 'demand' not in item:
                            item.demand = {}
                        if demand_maximum is not None:
                            item.demand.maximum = parse_duration(demand_maximum)
                            item.demand.maximum_str = demand_maximum
                        if demand_reorder_point is not None:
                            item.demand.reorder_point = parse_duration(demand_reorder_point)
                            item.demand.reorder_point_str = demand_reorder_point

                supply_suggested = self.get_supply_suggested(item)
                if supply_suggested is not None:
                    item.supply_suggested = supply_suggested
                elif 'supply_suggested' in item:
                    del item.supply_suggested
            self.model.datasource = mis['items']


    def async

    def get_supply_suggested(self, item):
        if item.method in ['itemdemand', 'demand'] and 'demand' in item and 'covered' in item:
            if 'demand' in item and 'maximum' in item.demand:
                demand_maximum = item.demand.maximum
            else:
                demand_maximum = self.demand_maximum

            if 'demand' in item and 'reorder_point' in item.demand:
                demand_reorder_point = item.demand.reorder_point
            else:
                demand_reorder_point = self.demand_reorder_point

            if demand_reorder_point is not None and demand_reorder_point > item.covered < demand_maximum:
                return round(D((demand_maximum - item.covered) / item.demand.period) * item.demand.n, 3)
            elif demand_reorder_point is None and item.covered < demand_maximum:
                return round(D((demand_maximum - item.covered) / item.demand.period) * item.demand.n, 3)
        elif item.method == 'maximum' and 'maximum' in item:
            if item.inventory < item.maximum and 'reorder_point' in item and item.reorder_point > item.inventory:
                return item.maximum - item.inventory
            elif item.inventory < item.maximum and 'reorder_point' not in item:
                return item.maximum - item.inventory


class Manage_Items_Supply(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(1600, 900)
        self.setWindowTitle('valentine.Items')
        cwidget = Widget()
        self.setCentralWidget(cwidget)
        from katherine import d6, pymysql
        d6.ping(True)
        d6_cursor = d6.cursor(pymysql.cursors.SSDictCursor)
        d6_cursor.execute('select distinct item.sku, item.description from itzamara.item '
                          'inner join valentine.method_evaluation_supply as method '
                          'on method.item_sku = item.sku where storage_id = \'42-3\' ')
        items = list(d6_cursor.fetchall())
        cwidget.manage_items_supply = dict(
            {'items': items, 'storage': d1.valentine.storage.find_one({'id': '42-3'})}
        )
        d6.close()


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    v = Manage_Items_Supply()
    v.show()
    sys.exit(app.exec_())
