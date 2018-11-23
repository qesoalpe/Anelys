from .table import Columns
from dict import Dict
from PySide2.QtCore import QModelIndex, Qt, QAbstractItemModel


class Item():
    def __init__(self, data, kwchildren='children', tree=None):
        self.parent = None
        self.children = list()
        self.tree = tree
        if data is not None and isinstance(data, Dict):
            if kwchildren in data:
                for child in data[kwchildren]:
                    child = Item(child, kwchildren, tree)
                    child.parent = self
                    self.children.append(child)
        self._data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def appendChild(self, child):
        if not isinstance(child, Item):
            child = Item(child, self.tree.kwchildren, self.tree)
            child.parent = self
        self.children.append(child)

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        if self.tree is not None and isinstance(self.tree, Tree):
            return len(self.tree.columns)
        else:
            return 0

    def child(self, index):
        if len(self.children) > index:
            return self.children[index]
        else:
            return None

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)
        else:
            return 0


class Tree(QAbstractItemModel):
    def __init__(self):
        QAbstractItemModel.__init__(self)
        self.columns = Columns(self)
        self.classitem = Item
        self._rootitem = None
        self.kwchildren = 'children'

    def rowCount(self, parent):
        if not parent.isValid():
            parentItem = self.rootitem
        else:
            parentItem = parent.internalPointer()
        if parentItem is not None:
            return parentItem.childCount()
        else:
            return 0

    def columnCount(self, parent=None):
        return len(self.columns)

    @property
    def rootitem(self):
        return self._rootitem

    @rootitem.setter
    def rootitem(self, rootitem):
        if not isinstance(rootitem, self.classitem):
            rootitem = self.classitem(rootitem, self.kwchildren, tree=self)
        self._rootitem = rootitem
        self.notify_update_all()

    def notify_update_all(self):
        self.modelReset.emit()

    @property
    def datasoure(self):
        if self.rootitem is not None and isinstance(self.rootitem, self.classitem):
            return self.rootitem.data.children
        else:
            return None

    def index(self, row, column, parent):
        if not parent.isValid():
            parentItem = self.rootitem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.rootitem:
            return QModelIndex()
        else:
            return self.createIndex(parentItem.row(), 0, parentItem)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            column = self.columns[section]
            if column.name is not None:
                return column.name
            else:
                return column.fieldname

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = index.internalPointer()
        column = self.columns[index.column()]
        data = column.get_data(item.data)
        if data is not None:
            return column.format_data_display(data)
