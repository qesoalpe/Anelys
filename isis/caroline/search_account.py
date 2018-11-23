from isis.dialog_search_text import Dialog_Search_Text, Data_Table_Model
from sarah.acp_bson import Client


class Search_Account(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_caroline = None

    def searching(self, e):
        if self.agent_caroline is None:
            self.agent_caroline = Client('isis.caroline.search_account', 'caroline')
        msg = {'type_message': 'find', 'type': 'caroline/account', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_caroline.send_msg(msg)
        e['list'] = answer['result']
        table = Data_Table_Model()
        e['table'] = table
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('account_type', str)
        table.columns.add('name', str)
        for account in e['list']:
            row = table.newrow()
            if 'id' in account:
                row['id'] = account['id']
            if 'type' in account:
                row['type'] = account['type']
            if 'account_type' in account:
                row['account_type'] = account['account_type']
            if 'name' in account:
                row['name'] = account['name']
