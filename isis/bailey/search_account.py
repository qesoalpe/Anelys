from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table
from dict import Dict as dict
from katherine import d6


class Search_Account(Dialog_Search_Text):
    def __init__(self, *args, **kwargs):
        Dialog_Search_Text.__init__(self, *args, **kwargs)
        self.setWindowTitle(self.__class__.__name__)
        self.resize(600, 600)

    def searching(self, e):
        d6.ping(True)
        d6_cursor = d6.cursor()
        d6_cursor.execute('select id, number, clabe, bank_name, titular_name from bailey.account '
                          'where CONCAT(titular_name, " ", number) like %s;',
                          ('%' + e.text.replace(' ', '%') + '%',))

        accounts = [dict({'id': id, 'number': number, 'clabe': clabe, 'bank': {'name': bank_name},
                          'titular': {'name': titular_name}})
                    for id, number, clabe, bank_name, titular_name in d6_cursor]
        getter_titular = lambda x: x.titular.name if 'titular' in x and 'name' in x.titular else None
        accounts.sort(key=lambda x: getter_titular(x) + x.number)
        e.list = accounts
        e.table = Table()
        e.table.columns.add('id', str)
        e.table.columns.add('number', str)
        e.table.columns.add('clabe', str)
        e.table.columns.add('titular', str)
        e.table.columns.add('bank', str)
        e.table.columns['titular'].getter_data = getter_titular
        e.table.columns['bank'].getter_data = lambda x: x.bank.name if 'bank' in x and 'name' in x.bank else None

        e.table.datasource = e.list
