from isis.dialog_select_table import Dialog_Select_Table
from isis.data_model.table import Table
from sarah.acp_bson import Client
from decimal import Decimal as D


class Select_Document_Purchase_Without_Purchase(Dialog_Select_Table):
    def __init__(self, parent=None, provider=None):
        self.provider = provider
        self.agent_bethesda = Client('Select_Document_Purchase_Without_Purchase', 'bethesda')
        Dialog_Select_Table.__init__(self, parent)

    def loading(self, e):
        msg = {'type_message': 'request', 'request_type': 'get', 'get': 'bethesda/documents_purchase_without_purchase'}
        if self.provider is not None:
            msg['query'] = {'provider': self.provider}
        answer = self.agent_bethesda(msg)
        table = Table()
        table.columns.add('id', str)
        # table.columns.add('type', str)
        table.columns.add('type', str)
        if self.provider is None:
            table.columns.add('provider', str)
        table.columns.add('folio', str)
        table.columns.add('datetime', str)
        table.columns.add('amount', D, 'c')

        def gt_type(data):
            if 'document_type' in data:
                return data.document_type
            elif 'document_purchase_type' in data:
                return data.document_purchase_type
            elif 'type' in data:
                return data.type

        def gt_provider(data):
            if 'provider' in data:
                provider = data.provider
                if 'business_name' in provider:
                    return provider.business_name
                elif 'name' in provider:
                    return provider.name
                elif 'rfc' in provider:
                    return provider.rfc
                elif 'id' in provider:
                    return provider.id
                else:
                    return provider

        table.columns['type'].getter_data = gt_type
        if self.provider is None:
            table.columns['provider'].getter_data = gt_provider
        table.columns['datetime'].getter_data = lambda x: x.datetime if 'datetime' in x else x.date if 'date' in x else None
        table.columns['amount'].getter_data = lambda x: x.amount if 'amount' in x else x.total if 'total' in x else None

        e.list = answer.result
        e.table = table
        table.datasource = e.list

    def selecting(self, index):
        doc = self.selectablelist[index]
        if 'document_purchase_type' in doc:
            doc_type = doc['document_purchase_type']
        elif 'document_type' in doc:
            doc_type = doc['document_type']
        else:
            return doc
        msg = {'type_message': 'find_one', 'type': doc_type, 'query': {'id': doc['id']}}
        answer = self.agent_bethesda(msg)
        if 'result' in answer and answer['result'] is not None:
            return answer['result']
        else:
            return doc
