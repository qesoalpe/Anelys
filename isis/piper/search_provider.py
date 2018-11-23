from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table
from sarah.acp_bson import Client


class Search_Provider(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_piper = None

    def searching(self, e):
        if self.agent_piper is None:
            self.agent_piper = Client(Search_Provider.APP_ID, '/piper')
        msg = {'type_message': 'find', 'type': 'piper/provider', 'query': {'name': {'!like': e['text']}}}
        answer = self.agent_piper.send_msg(msg)
        e['list'] = answer['result']
        table = Table()
        e['table'] = table
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('name', str)
        table.columns.add('rfc', str)
        table.datasource = e.list

    APP_ID = 'isis.piper.search_provider'


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Search_Provider()
    sys.exit(vv.exec_())
