def _process_object(x, memo):
    y = memo.get(id(x), None)
    if y is None:
        if isinstance(x, list) and not isinstance(x, List):
            memo[id(x)] = List(x, memo)
        elif isinstance(x, dict) and not isinstance(x, Dict):
            memo[id(x)] = Dict(x, memo)
        else:
            memo[id(x)] = x


class List(list):
    def __init__(self, origen=None, memo=None):
        list.__init__(self)
        from collections import Iterable
        from types import GeneratorType
        if origen is not None and isinstance(origen, Iterable) and not isinstance(origen, GeneratorType):
            if memo is None:
                memo = {}
            memo[id(origen)] = self
            for item in origen:
                if id(item) in memo:
                    list.append(self, memo[id(item)])
                else:
                    _process_object(item, memo)
                    list.append(self, memo[id(item)])
        elif origen is not None and isinstance(origen, GeneratorType):
            memo = {id(self): self}
            for item in origen:
                if isinstance(item, dict) and not isinstance(item, Dict):
                    item = Dict(item)
                _process_object(item, memo)
                list.append(self, memo[id(item)])

    def __deepcopy__(self, memo):
        from copy import deepcopy
        d = id(self)

        y = memo.get(d, None)
        if y is not None:
            return y

        y = List()
        memo[d] = y

        for item in self:
            y.append(deepcopy(item, memo))
        return y

    def append(self, x):
        memo = {id(self): self}
        _process_object(x, memo)
        list.append(self, memo[id(x)])

    def __setitem__(self, i, o):
        if not isinstance(i, int):
            raise TypeError('list indices must be integers or slices, not str')
        if not (0 <= i < len(self)):
            raise IndexError('list assignment index out of range')
        memo = {id(self): self}
        _process_object(o, memo)
        list.__setitem__(self, i, o)


class Dict(dict):
    def __init__(self, origen=None, memo=None):
        dict.__init__(self)

        if origen is not None and isinstance(origen, dict):
            if memo is None:
                memo = {}

            memo[id(self)] = self
            memo[id(origen)] = self

            for k, v in origen.items():
                if id(v) in memo:
                    self[k] = memo[id(v)]
                else:
                    _process_object(v, memo)
                    self[k] = memo[id(v)]

    def __getattr__(self, item):
        if item == '_type_marker':
            return None
        return self.__getitem__(item)

    def __delattr__(self, item):
        del self[item]

    def __setattr__(self, key, value):
        memo = {id(self): self}
        _process_object(value, memo)
        dict.__setitem__(self, key, memo[id(value)])

    def __setitem__(self, key, value):
        memo = {id(self): self}
        _process_object(value, memo)
        dict.__setitem__(self, key, memo[id(value)])

    def __deepcopy__(self, memo):
        from copy import deepcopy
        d = id(self)

        y = memo.get(d, None)
        if y is not None:
            return y

        y = Dict()
        memo[d] = y
        for k, v in self.items():
            y[deepcopy(k, memo)] = deepcopy(v, memo)
        return y
