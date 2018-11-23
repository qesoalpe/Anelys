from sarah.acp_bson import Client
from PySide.QtCore import *
from PySide.QtGui import *
from isis.data_model.table import Table


class New_Task(QDialog):
    pass


COLUMN_ID = 0
COLUMN_TYPE = 1
COLUMN_TITLE = 2
COLUMN_DUE_DATETIME = 3
COLUMN_STATUS = 4


class Tasks_Table_Model(Table):
    def __init__(self):
        Table.__init__(self, 'Tasks')
        self.columns.add('id', str)
        self.columns.add('type', str)
        self.columns.add('title', str)
        self.columns.add('due_datetime', str)
        self.columns.add('status', str)


class Main_Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 500)
        self.setWindowTitle('tasks')
        self.cwidget = QWidget(self)
        self.setCentralWidget(self.cwidget)

        self.mainlayout = QGridLayout(self.cwidget)
        self.tableview = QTableView(self.cwidget)
        self.mainlayout.addWidget(self.tableview, 0, 0)
        self.create_toolbars()
        self.agent_odette = Client('isis.tasks', 'odette')
        msg = {'type_message': 'find', 'type': 'odette/task', 'query': {'finished': False}}
        answer = self.agent_odette.send_msg(msg)
        self.task = answer['result']
        self.model = Tasks_Table_Model()
        self.model.rows = self.task
        self.tableview.setModel(self.model)
        self.tableview.resizeColumnsToContents()

    def create_toolbars(self):
        tasks_toolbar = self.addToolBar('tasks')
        action_new = QAction('new', tasks_toolbar)
        tasks_toolbar.addAction(action_new)
        action_new.triggered.connect(self.handle_action_new)

    def handle_action_new(self):
        dialog = New_Task(self)
        dialog.setModal(True)
        dialog.show()



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    vv = Main_Window()
    vv.show()
    sys.exit(app.exec_())




# class Tasks_Table_Mode(QAbstractTableModel):
#     def __init__(self):
#         QAbstractTableModel.__init__(self)
#         self.rows = list()
#     def data(self, index, role):
#         if role == Qt.DisplayRole:
#             row = self.rows[index.row()]
#             column = index.column()
#             if column == COLUMN_ID:
#                 if 'id' in row:
#                     return row['id']
#             elif column == COLUMN_TYPE:
#                 if 'type' in row:
#                     return row['type']
#             elif column == COLUMN_TITLE:
#                 if 'title' in row:
#                     return row['title']
#             elif column == COLUMN_DUE_DATETIME:
#                 if 'due_datetime' in row:
#                     return row['due_datetime']
#             elif column == COLUMN_STATUS:
#                 if 'status' in row:
#                     return row['status']
#
#     def headerData(self, section, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             if section == COLUMN_ID:
#                 return 'id'
#             elif section == COLUMN_TYPE:
#                 return 'type'
#             elif section == COLUMN_TITLE:
#                 return 'title'
#             elif section == COLUMN_DUE_DATETIME:
#                 return 'due_datetime'
#             elif section == COLUMN_STATUS:
#                 return 'status'
#
#     def rowCount(self, parent):
#         return len(self.rows)
#
#     def columnCount(self, parent):
#         return 5