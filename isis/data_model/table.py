from PySide2.QtCore import QAbstractTableModel, Qt, QModelIndex
from decimal import Decimal
from isis.utils import format_currency
list_cls = list
from dict import Dict, Dict as dict, List as list
from isis.event import Event


class Column:
    def __init__(self, fieldname=None, type=None, columns=None, format=None):
        self.fieldname = fieldname
        self.type = type
        self.columns = columns
        self.format = format
        self._readonly = None
        self.name = None
        self.getter_data = None

    @property
    def index(self):
        if self.columns is not None:
            return self.columns._columns.index(self)
        else:
            return -1

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, readonly):
        if isinstance(readonly, bool):
            self._readonly = readonly
        else:
            raise Exception()

    def format_data_display(self, data):
        column = self
        if data is None:
            return None
        if column.type == str:
            if isinstance(data, str):
                return data
            else:
                return str(data)
        elif column.type == Decimal:
            if column.format is not None:
                if callable(column.format):
                    return column.format(data)
                elif isinstance(column.format, str):
                    if column.format.lower() == 'c':
                        if isinstance(data, (Decimal, int, float)):
                            return format_currency(data)
                    else:
                        if isinstance(data, (Decimal, int, float)):
                            from babel.numbers import format_decimal
                            return format_decimal(data, column.format, 'es_mx')

            if isinstance(data, str):
                return data
            else:
                return str(data)
        elif column.type == bool:
            if data:
                return 'True'
            else:
                return 'False'
        elif column.type == int:
            return str(data)

    def get_data(self, row):
        column = self
        if column.getter_data is not None and callable(column.getter_data):
            return column.getter_data(row)
        elif column.getter_data is not None and isinstance(column.getter_data, list_cls):
            getter_list = column.getter_data
            for gl in getter_list:
                if gl in row:
                    return row[gl]
        elif column.getter_data is not None and isinstance(column.getter_data, str) and column.getter_data in row:
            return row[column.getter_data]
        elif column.fieldname in row:
            return row[column.fieldname]

    format_data_edit = format_data_display


class Columns:
    def __init__(self, table=None):
        self.table = table
        self._columns = list()
        self.event_column_appended = Event()

    def add(self, fieldname=None, type=None, format=None, column=None):
        if fieldname is None and type is None and column is None:
            column = Column(columns=self)
            self._columns.append(column)
            # if self.table is not None:
            #     column.readonly = self.table.readonly
            # return column
        elif column is None:
            newcolumn = Column(columns=self)
            newcolumn.fieldname = fieldname
            newcolumn.type = type
            newcolumn.format = format
            self._columns.append(newcolumn)
            # if self.table is not None:
            #     column.readonly = self.table.readonly
            # return newcolumn
        elif column is not None and isinstance(column, Column):
            self._columns.append(column)
            # if self.table is not None:
            #     column.readonly = self.table.readonly
            # return column

    def append(self, column):
        return self.add(column=column)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._columns[item]
        elif isinstance(item, str):
            for column in self._columns:
                if column.fieldname is not None and column.fieldname == item:
                    return column
            else:
                raise KeyError(item)
        else:
            raise KeyError(item)

    def __len__(self):
        return len(self._columns)


class Table(QAbstractTableModel):
    def __init__(self, name=None):
        QAbstractTableModel.__init__(self)
        self.rows = list()
        self.columns = Columns(self)
        self.name = name if name is not None else ''
        self._readonly = False
        self._with_new_empty_row = False
        self.creating_row = Event()
        self.before_changing_value = Event()
        self.after_changing_value = Event()
        self.any_change_in_datasource = Event()
        self.modelReset.connect(self.any_change_in_datasource)
        self.rowsInserted.connect(self.any_change_in_datasource)
        self.rowsRemoved.connect(self.any_change_in_datasource)
        self.dataChanged.connect(self.any_change_in_datasource)

    def clear(self):
        self.datasource = list()

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, readonly):
        self._readonly = readonly
        self.update_all()

    @property
    def with_new_empty_row(self):
        return self._with_new_empty_row

    @with_new_empty_row.setter
    def with_new_empty_row(self, value):
        if value is not None and isinstance(value, bool) and value != self.with_new_empty_row:
            self._with_new_empty_row = value
            self.update_all()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            column = self.columns[section]
            if isinstance(column, Column):
                if column.name is not None and column.name:
                    return column.name
                elif column.fieldname is not None:
                    return column.fieldname

    def _is_the_new_empty_row(self, index):
        return len(self.datasource) == index

    is_the_new_empty_row = _is_the_new_empty_row

    def data(self, index, role):
        if self.with_new_empty_row and self._is_the_new_empty_row(index.row()):
            return None
        row = self.rows[index.row()]
        column = self.columns[index.column()]

        if role == Qt.DisplayRole:
            data = column.get_data(row)
            if data is not None:
                return column.format_data_display(data)

        elif role == Qt.EditRole:
            data = column.get_data(row)
            if data is not None:
                return column.format_data_edit(data)

    def rowCount(self, parent=None):
        if self.rows is not None:
            if self.with_new_empty_row:
                return len(self.rows) + 1
            else:
                return len(self.rows)
        else:
            return 0

    def columnCount(self, parent=None):
        return len(self.columns)

    def flags(self, index):
        column = self.columns[index.column()]
        # row = self.rows[index.row()]
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if column.readonly is not None:
            if not column.readonly:
                flags |= Qt.ItemIsEditable
        elif self.readonly is not None:
            if not self.readonly:
                flags |= Qt.ItemIsEditable

        if hasattr(self, 'row_readonly') and callable(self.row_readonly):
            if not self.row_readonly(index.row()):
                flags |= Qt.ItemIsEditable

        if self.is_the_new_empty_row(index.row()) and not flags & Qt.ItemIsEditable and column.readonly is None:
            flags |= Qt.ItemIsEditable
        return flags

    def update_all(self):
        self.modelReset.emit()

    def notify_row_changed(self, x):
        if not isinstance(x, int):
            x = self.datasource.index(x)
        topleft = self.createIndex(x, 0)
        bottomright = self.createIndex(x, self.columnCount() - 1 if self.columnCount() > 0 else 0)
        self.dataChanged.emit(topleft, bottomright)

    def notify_data_changed(self, x, y):
        if not isinstance(x, int):
            x = self.datasource.index(x)
        if not isinstance(y, int):
            if isinstance(y, str):
                y = self.columns[y].index

    notifiy_cell_changed = notify_data_changed

    @property
    def datasource(self):
        return self.rows

    @datasource.setter
    def datasource(self, datasource):
        self.rows = datasource
        self.modelReset.emit()

    def add_row(self, row=None):
        if row is None:
            row = Dict()
        i = self.rowCount()
        self.beginInsertRows(QModelIndex(), i, i)
        self.datasource.append(row)
        self.endInsertRows()

    def insert_row(self, r, i):
        self.beginInsertRows(QModelIndex(), i, i)
        self.datasource.append(r)
        self.endInsertRows()

    def remove_data(self, index):
        if not isinstance(index, int):
            index = self.datasource.index(index)
        self.beginRemoveRows(QModelIndex(), index, index)
        del self.datasource[index]
        self.endRemoveRows()

    remove_row = remove_data

    def setData(self, index, value, role=Qt.EditRole):
        column = self.columns[index.column()]

        def format(value):
            if column.type == Decimal and isinstance(value, str):
                if value:
                    from babel.numbers import parse_decimal
                    value = value.replace('$', '')
                    return parse_decimal(value, locale='es_mx')
            else:
                return value
        value = format(value)
        if self._is_the_new_empty_row(index.row()):
            if len(self.creating_row):
                # self.before_changing_value(index.row(), value)
                row = self.creating_row(column, value)
                # self.after_changing_value(index.row(), value)
                if row is not None:
                    self.add_row(row)
                    return True
                else:
                    return False
            else:
                self.datasource.append(dict())
                self.before_changing_value(index.row(), column, value)
                if hasattr(column, 'changing_value'):
                    handled = column.changing_value(index.row(), value)
                elif hasattr(column, 'changing_item_value'):
                    handled = column.changing_item_value(self.datasource[index.row()], value)
                else:
                    item = self.datasource[index.row()]
                    item[column.fieldname] = value
                    handled = True
                self.after_changing_value(index.row(), column, value)
                if handled is None or handled:
                    self.notify_row_changed(index.row())
                    self.beginInsertRows(QModelIndex(), index.row() + 1, index.row() + 1)
                    self.endInsertRows()
                    return True
                else:
                    del self.datasource[index.row()]
                    return False
        else:
            self.before_changing_value(index.row(), column, value)
            if hasattr(column, 'changing_value') and callable(column.changing_value):
                handled = column.changing_value(index.row(), value)
            elif hasattr(column, 'changing_item_value'):
                handled = column.changing_item_value(self.datasource[index.row()], value)
            else:
                item = self.datasource[index.row()]
                item[column.fieldname] = value
                handled = True
            self.after_changing_value(index.row(), value)
            if handled is None or handled:
                self.notify_row_changed(index.row())
                return True
            else:
                return False


__all__ = ['Table', 'Event', 'Column', 'Columns']
