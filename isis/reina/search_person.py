from isis.dialog_search_text import Dialog_Search_Text, Data_Table_Model
from sarah.acp_bson import Client


class Search_Person(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_reina = Client('isis.reina.search_person', 'reina')

    def searching(self, e):
        msg = {'type_message': 'find', 'type': 'reina/person', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_reina(msg)
        e['list'] = answer['result']
        table = Data_Table_Model('persons')
        e['table'] = table
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('name', str)
        for person in e['list']:
            row = table.newrow()
            if 'id' in person:
                row['id'] = person['id']
            if 'type' in person:
                row['type'] = person['type']
            if 'name' in person:
                row['name'] = person['name']
