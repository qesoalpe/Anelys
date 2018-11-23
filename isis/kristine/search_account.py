from isis.dialog_search_text import Dialog_Search_Text
from isis.data_model.table import Table
from katherine import d1
from dict import Dict
from copy import deepcopy

def project(d, p):
    for k in list(d.keys()):
        if k not in p:
            del d[k]


def populate_children(account):
    children = list()
    for child in d1.kristine.account.find({'parent.id': account.id}, {'_id': False}):
        child.parent = account
        children.append(child)
    if len(children):
        for child in children:
            populate_children(child)
        account.children = children

root = Dict({'id': 'root'})

populate_children(root)


def get_accounts(accounts, parent):
    rr = list()
    for account in accounts:
        if 'children' in account:
            children = account.children
            del account.children
        else:
            children = None
        if 'parent' in account:
            _parent = account.parent
            del account.parent
        else:
            _parent = None
        r = deepcopy(account)
        if children is not None: account.children = children
        if _parent is not None: account.parent = _parent

        project(r, ['id', 'name', 'type', 'fullpath'])
        if parent.fullpath == '/':
            r.fullpath = parent.fullpath + r.name
        else:
            r.fullpath = parent.fullpath + '/' + r.name
        rr.append(r)
        if 'children' in account and len(account.children):
            rr.extend(get_accounts(account.children, r))
    return rr

accounts = get_accounts(root.children, Dict({'fullpath': '/'}))
from sorter import Sorter
sorter = Sorter()
sorter.columns.add('fullpath', 1)
sorter.sort(accounts)

# pprint(accounts)

import re


class Search_Account(Dialog_Search_Text):
    def searching(self, e):
        s = re.compile('.*' + e.text.replace(' ', '.*') + '.*', re.I)
        result = list(filter(lambda x: len(s.findall(x.fullpath)), accounts))

        table = Table()
        table.columns.add('id', str)
        table.columns.add('fullpath', str)
        table.datasource = result

        e.list = result
        e.table = table
