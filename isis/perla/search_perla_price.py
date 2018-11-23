from isis.dialog_search_text import Dialog_Search_Text, Data_Table_Model
from sarah.acp_bson import Client
from decimal import Decimal

class Search_Perla_Price(Dialog_Search_Text):
    def __init__(self, parent=None, agent_perla=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_perla = agent_perla

    def searching(self, e):
        if self.agent_perla is None:
            self.agent_perla = Client(self.APP_ID_DOC, 'perla')
        msg = {'type_message': 'find', 'type': 'perla/price', 'query': {'description': {'!like': e['text']}}}
        answer = self.agent_perla.send_msg(msg)
        e['list'] = answer['result']
        table = Data_Table_Model()
        e['table'] = table
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('description', str)
        table.columns.add('value', Decimal, formatstr='c')
        for price in e['list']:
            row = table.newrow()
            if 'id' in price:
                row['id'] = price['id']
            if 'type' in price:
                row['type'] = price['type']
            if 'description' in price:
                row['description'] = price['description']
            if 'value' in price:
                row['value'] = price['value']

    APP_ID_DOC = {'id': 'isis.search_perla_price'}

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Search_Perla_Price()
    vv.show()
    sys.exit(app.exec_())