from sarah.acp_bson import Client
from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table


class Search_Client(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_caroline = Client('Search_Client', 'caroline')

    def searching(self, e):
        msg = {'type_message': 'find', 'type': 'caroline/client',
               'query': {'name': {'!like': e['text']}}}
        answer = self.agent_caroline(msg)

        table = Table()
        table.columns.add('id', str)
        table.columns.add('name', str)
        table.columns.add('rfc', str)

        e['list'] = answer['result']
        e['table'] = table
        table.columns['name'].getter_data = ['business_name', 'name']
