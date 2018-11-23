from isis.dialog_select_table import Dialog_Select_Table, Data_Table_Model
from sarah.acp_bson import Client

me = {'id': '3-1'}


class Select_Own_Account(Dialog_Select_Table):
    def __init__(self, parent=None):
        self.agent_bailey = Client('Select_Own_Account', 'bailey')
        Dialog_Select_Table.__init__(self, parent)

    def loading(self, e):
        msg = {'type_message': 'find', 'type': 'bailey/account', 'query': {'titular': me}}
        answer = self.agent_bailey(msg)
        table = Data_Table_Model()
        table.columns.add('bank', str)
        table.columns.add('number', str)
        table.columns.add('clabe', str)
        e['table'] = table
        e['list'] = answer['result']
        for account in e['list']:
            row = table.newrow()
            if 'number' in account:
                row['number'] = account['number']
            elif 'num' in account:
                row['number'] = account['num']

            if 'bank' in account and 'name' in account['bank']:
                row['bank'] = account['bank']['name']
            elif 'bank' in account and 'id' in account['bank']:
                row['bank'] = account['bank']['id']
            elif 'bank_name' in account:
                row['bank'] = account['bank_name']
            elif 'bank_id' in account:
                row['bank'] = account['bank_id']

            if 'clabe' in account:
                row['clabe'] = account['clabe']