from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table
from sarah.acp_bson import Client


class Search_Item(Dialog_Search_Text):
    def __init__(self, parent=None):
        Dialog_Search_Text.__init__(self, parent)
        self.agent_itzamara = None
        self.store = None
        self.search_by_sku = True
        self.search_by_code_ref = True
        self.agent_itzamara = Client(Search_Item.APP_ID, 'itzamara')

    def searching(self, e):
        if self.search_by_sku:
            msg = {'type_message': 'find_one', 'type': 'itzamara/item', 'query': {'sku': e['text']}}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer['result'] is not None:
                e['selected'] = answer['result']
                return
        if self.search_by_code_ref:
            msg = {'type_message': 'request', 'request_type': 'get', 'get': 'itzamara/item_related_to_code_ref',
                   'code_ref': e.text}
            answer = self.agent_itzamara(msg)
            if 'result' in answer and answer.result is not None:
                e.selected = answer.result
                return
        msg = {'type_message': 'find', 'type': 'itzamara/item', 'query': {'description': {'!like': e['text']}}}
        if self.store is not None:
            msg['query']['store'] = self.store
        answer = self.agent_itzamara.send_msg(msg)
        e['list'] = answer['result']
        table = Table()
        e['table'] = table
        table.columns.add('sku', str)
        table.columns.add('description', str)
        table.datasource = e.list

    APP_ID = 'isis.itzamara.Search_Item'
