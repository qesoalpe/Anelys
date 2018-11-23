from dict import Dict as dict


class Filter_Mongo:
    def __init__(self):
        self.dict = dict()
        self.tree = dict()
        self.fields = list()

    def parse_anelys_query(self, query, path=None):
        for k1, v1 in query.items():
            if k1 == '!or':
                f = Filter_Or_Mongo()
                self.tree['$or'] = f
                self.dict['$or'] = f.list
                f.parse_anelys_query(v1)
            elif k1 == '!and':
                f = Filter_And_Mongo()
                self.tree['$and'] = f
                self.dict['$and'] = f.list
                f.parse_anelys_query(v1)
            elif k1 == '!exists':
                assert isinstance(v1, bool)
                assert path is not None
                assert path not in self.dict
                self.dict[path] = {'$exists': v1}
            elif isinstance(v1, dict):
                filter = Filter_Mongo()
                self.tree[k1] = filter
                filter.dict = self.dict
                filter.fields = self.fields
                if path:
                    k1 = path + '.' + k1
                filter.parse_anelys_query(v1, k1)
            else:  # if isinstance(v1, str):
                if path:
                    k1 = path + '.' + k1
                self.dict[k1] = v1


class Filter_And_Mongo:
    def __init__(self):
        self.list = list()
        self.tree = list()

    def parse_anelys_query(self, query, path=None):
        for q in query:
            f = Filter_Mongo()
            f.parse_anelys_query(q)
            self.list.append(f.dict)
            self.tree.append(f)


class Filter_Or_Mongo:
    def __init__(self):
        self.list = list()
        self.tree = list()

    def parse_anelys_query(self, query, path=None):
        for q in query:
            f = Filter_Mongo()
            f.parse_anelys_query(q)
            self.list.append(f.dict)
            self.tree.append(f)
