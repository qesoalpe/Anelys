from isis.dialog_search_text import Dialog_Search_Text, Data_Table_Model
from sarah.acp_bson import Client

class Search_Item_List(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_itzamara = None

    def searching(self, e):
        if self.agent_itzamara is None:
            self.agent_itzamara = Client('isis.itzamara.search_item_list', 'itzamara')
        msg = {'type_message': 'find', 'type': 'itzamara/item_list', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_itzamara.send_msg(msg)
        table = Data_Table_Model()
        e['table'] = table
        e['list'] = answer['result']
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('name', str)
        for itemlist in e['list']:
            row = table.newrow()
            if 'id' in itemlist:
                row['id'] = itemlist['id']
            if 'type' in itemlist:
                row['type'] = itemlist['type']
            if 'name' in itemlist:
                row['name'] = itemlist['name']
