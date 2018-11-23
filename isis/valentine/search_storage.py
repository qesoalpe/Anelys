from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table
from sarah.acp_bson import Client


class Search_Storage(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.resize(850, 550)
        self.setWindowTitle('Search_Storage')
        self.agent_valentine = None

    APP_ID = 'isis.valentine.search_storage'

    def searching(self, e):
        if self.agent_valentine is None:
            self.agent_valentine = Client(Search_Storage.APP_ID, 'valentine')
        msg = {'type_message': 'find', 'type': 'valentine/storage', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_valentine.send_msg(msg)
        e['list'] = answer['result']
        table = Table()
        e['table'] = table
        table.columns.add('id', str)
        # table.columns.add('type', str)
        table.columns.add('storage_type', str)
        table.columns.add('name', str)
        table.columns.add('address', str)
        table.datasource = e.list
        

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Search_Storage()
    vv.show()
    sys.exit(app.exec_())
