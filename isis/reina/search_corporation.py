from isis.dialog_search_text import Dialog_Search_Text, Data_Table_Model
from sarah.acp_bson import Client


class Search_Corporation(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_reina = Client('isis.reina.search_corporation', 'reina')

    def searching(self, e):
        msg = {'type_message': 'find', 'type': 'reina/corporation', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_reina(msg)
        table = Data_Table_Model()
        e['table'] = table
        e['list'] = answer['result']
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('business_name', str)
        table.columns.add('rfc', str)
        for corporation in e['list']:
            row = table.newrow()
            if 'id' in corporation:
                row['id'] = corporation['id']
            if 'type' in corporation:
                row['type'] = corporation['type']
            if 'business_name' in corporation:
                row['business_name'] = corporation['business_name']
            elif 'name' in corporation:
                row['business_name'] = corporation['name']
            if 'rfc' in corporation:
                row['rfc'] = corporation['rfc']
