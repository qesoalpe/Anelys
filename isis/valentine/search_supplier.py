from isis.dialog_search_text import Dialog_Search_Text
from sarah.acp_bson import Client
import re
from isis.data_model.table import Table
agent_valentine = Client('', 'valentine')


class Search_Supplier(Dialog_Search_Text):
    def searching(self, e):
        msg = {'type_message': 'find', 'type': 'valentine/supplier',
               'query': {'name': re.compile('.*' + re.escape(e.text).replace(r'\ ', '.*') + '.*')}}
        answer = agent_valentine(msg)
        e.list = answer.result
        e.table = Table()
        e.table.columns.add('id', str)
        e.table.columns.add('type', str)
        e.table.columns.add('name', str)
        e.table.columns['type'].getter_data = ['supplier_type', 'type']
        e.table.datasource = e.list
