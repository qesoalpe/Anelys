from PySide2.QtCore import Qt
from sarah.acp_bson import Client
from isis.itzamara.search_item import Search_Item
from isis.data_model.table import Table
from isis.dialog import Dialog
from isis.table_view import Table_View
from isis.v_box_layout import V_Box_Layout

class Model_Items(Table):
    def __init__(self, *args, **kwargs):
        Table.__init__(self)
        self.columns.add('sku', str)
        self.columns.add('description', str)

        self.columns['sku'].changing_value = self.handle_changing_sku
        self.columns['description'].changing_value = self.handle_changing_description

        self.creating_row.suscribe(self.handle_creating_row)
        self.datasource = list()
        self.parent_gui = None
        self.with_new_empty_row = True

    def handle_changing_sku(self, i, value):
        item = self.datasource[i]
        agent_itzamara = Client('item_list', 'itzamara')
        if value is not None and value:
            if 'sku' not in item or value != item['sku']:
                answer = agent_itzamara({'type_message': 'find_one', 'type': 'itzamara/item',
                                         'query': {'sku': value}})
                if 'result' in answer and answer['result'] is not None:
                    self.datasource[i] = answer.result
                else:
                    item.clear()
        else:
            item.clear()

    def handle_changing_description(self, i, value):
        item = self.datasource[i]
        if value is not None and value:
            if 'description' not in item or value != item['description']:
                searcher = Search_Item(self.parent_gui)
                result = searcher.search(value)
                if result is not None:
                    self.datasource[i] = result
                else:
                    item.clear()
        else:
            item.clear()

    def handle_creating_row(self, column, value):
        if column.fieldname == 'sku':
            agent_itzamara = Client('item_list', 'itzamara')
            answer = agent_itzamara({'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': value}})
            if 'result' in answer and answer.result is not None:
                return answer.result
        elif column.fieldname == 'description':  # description
            searcher = Search_Item(self.parent_gui)
            result = searcher.search(value)
            if result is not None:
                return result

    item_updated = Table.notify_row_changed
    insert = Table.insert_row
    add = Table.add_row
    remove = Table.remove_row


class Table_View_Items(Table_View):
    def __init__(self, parent=None):
        Table_View.__init__(self, parent)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.SingleSelection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            index = self.currentIndex()
            if index.isValid():
                model = self.model
                if len(model.datasource) > 0 and 0 <= index.row() < len(model.datasource):
                    model.remove(index.row())
                    return
        Table_View.keyPressEvent(self, event)


class Item_List(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle('Item_List')
        self.resize(400, 550)
        self.tableview = Table_View_Items(self)
        self.model = Model_Items(self)
        self.tableview.model = self.model

        layout_main = V_Box_Layout(self)
        layout_main.addWidget(self.tableview)

        self.setLayout(layout_main)

    @property
    def items(self):
        return self.model.datasource

    @items.setter
    def items(self, items):
        self.model.datasource = items


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)

    items = [{'sku': '1020', 'description': 'BT(10) Harina Maiz Maseca 1Kg'},
             {'sku': '1021', 'description': 'BT(10) Harina Trigo Diluvio 1kg'}]
    vv = Item_List()
    vv.items = items
    r = vv.exec_()
    from pprint import pprint
    pprint(vv.items)
    sys.exit(r)
