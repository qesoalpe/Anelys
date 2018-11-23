class Pool_Handler():
    def __init__(self, keyword_subpath='type_message'):
        self.subpaths = dict()
        self.keysubpath = keyword_subpath

    def __call__(self, msg, relativepath=None, authorativepath=None):
        if self.keysubpath in msg and msg[self.keysubpath] in self.subpaths:
            return self.subpaths[msg[self.keysubpath]](msg)

    def __setitem__(self, key, value):
        self.register_handler(key, value)

    def register_handler(self, path, handler):
        if isinstance(path, str):
            path = path.split('.')
        local = path[0].split('=')
        del path[0]
        if local[0] != self.keysubpath:
            raise Exception('Solo es permitido un solo keysubpath')
        if local[1] in self.subpaths:
            sub_handler = self.subpaths[local[1]]
            if isinstance(sub_handler, Pool_Handler):
                sub_handler.register_handler(path, handler)
            else:
                raise Exception('no se puede registrar otro path final con la misma direccion')
        else:
            if len(path) > 0:
                sub_handler = Pool_Handler(path[0].split('=')[0])
                sub_handler.register_handler(path, handler)
                self.subpaths[local[1]] = sub_handler
            else:
                self.subpaths[local[1]] = handler

    reg = register_handler
