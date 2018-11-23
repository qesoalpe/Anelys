from isis.table_view import Table_View
from isis.data_model.table import Table
from PySide2.QtWidgets import QStyledItemDelegate
from isis.combo_box import Combo_Box
from katherine import d6
from isis.message_box import Message_Box


class Code_Ref_Model(Table):
    def __init__(self, parent_gui=None):
        Table.__init__(self)
        self.columns.add('code_ref', str)
        self.columns.add('type', str)
        self.columns['code_ref'].changing_item_value = self.changing_item_value_code_ref
        self.with_new_empty_row = True
        self.datasource = list()
        self.item = None
        self.parent_gui = parent_gui

    def changing_item_value_code_ref(self, item, value):
        if value is None or not value:
            return False
        others_value = [i.code_ref for i in self.datasource if 'code_ref' in i and i is not item]
        if value in others_value:
            return False
        d6.ping(True)
        d6_cursor = d6.cursor()
        if self.item is not None and 'sku' in self.item:
            r = d6_cursor.execute('select sku from itzamara.code_ref where code_ref = %s and sku != %s limit 1;',
                                  (value, self.item.sku))
        else:
            r = d6_cursor.execute('select sku from itzamara.code_ref where code_ref =  %s limit 1;', (value,))
        d6.close()
        if r == 1:
            Message_Box.error(self.parent_gui, 'error', 'code_ref already exists in database')
            return False
        else:
            from PySide2.QtWidgets import QInputDialog
            v, yes = QInputDialog.getText(self.parent_gui, 'Verificar', 'introduce code_ref para verificar')
            if not yes or v != value:
                if 'code_ref' in item:
                    del item.code_ref
                    return True
                else:
                    return False
            if 'type' not in item:
                item.type = 'bar_code'
            item.code_ref = value
            return True

    def set_item(self, item):
        self.item = item


class Column_Code_Ref_Type_Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:
            editor = Combo_Box(parent)
            editor.addItems(['bar_code', 'code', 'code_bar_alias'])
            return editor


class Code_Ref_Table_View(Table_View):
    def __init__(self, *args, **kwargs):
        Table_View.__init__(self, *args, **kwargs)
        self.enable_delete_row_with_supr = True
        self.setItemDelegateForColumn(1, Column_Code_Ref_Type_Delegate())

