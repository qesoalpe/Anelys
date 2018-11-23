import io
from sarah.acp_bson import Client
agent = Client('fedra.io', 'valentine')




class BufferedIO(io.IOBase):
    def __init__(self):
        io.IOBase.__init__(self)
        self._length = None
        self._cursor = None
        self.id = None

    def read(self, size=-1):
        if size == -1:
            pass

    @property
    def length(self):
        if self._length is not None:
            return self._length
        elif self.id is not None:

        else:
            return None





def open(file, mode='r', encoding='utf8'):
    if 'b' in mode and 'r' in mode:
        if isinstance(file, dict):
            if 'id' in file:
