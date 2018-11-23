from isis.dialog_search_text import Dialog_Search_Text
from sarah.acp_bson import Client
import re

agent_serena = Client('', 'serena')


class Search_Store(Dialog_Search_Text):
    def searching(self, e):
        msg = dict({'type_message': 'find', 'type': 'serena/store',
                    'query': {'name': re.compile('.*' + re.escape(e.text).replace('\\ ', '.*') + '.*', re.I)}})
