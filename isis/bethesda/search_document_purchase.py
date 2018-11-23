from isis.dialog_search_text import Dialog_Search_Text
from katherine import d1
import dictutils
from isis.data_model.table import Table
from decimal import Decimal as D


class Search_Document_Purchase(Dialog_Search_Text):
    def searching(self, e):
        bethesda = d1.bethesda
        collections = [bethesda.invoice, bethesda.ticket, bethesda.remission, bethesda.note_credit, bethesda.sale_note]
        result = list()
        for coll in collections:
            result.extend(coll.find({'$or': [{'id': e.text}, {'folio': e.text}]}, {'_id': False}))
        result.sort(key=lambda x: x.datetime if 'datetime' in x else '')
        dictutils.list_float_to_dec(result)
        table = Table()
        table.columns.add('id', str)
        table.columns.add('type', str)
        table.columns.add('provider', str)
        table.columns.add('datetime', str)
        table.columns.add('amount', D, 'c')

        def getter_data_provider(row):
            if 'provider' in row:
                provider = row.provider
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

        table.columns['provider'].getter_data = getter_data_provider
        table.datasource = result
        e.table = table
        e.list = result
