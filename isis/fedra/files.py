from PySide2.QtCore import Qt
from isis.menu import Menu
from isis.data_model.table import Table
from isis.table_view import Table_View
from isis.file_dialog import File_Dialog
from humanize import naturalsize
from isis.main_window import Main_Window
from isis.widget import Widget
from isis.v_box_layout import V_Box_Layout
from katherine import d1, d2

class Model_Files(Table):
    def __init__(self):
        Table.__init__(self, 'files')
        self.columns.add('id', str)
        self.columns.add('name', str)
        self.columns.add('length', str, lambda x: naturalsize(x, True))
        self.columns.add('mime_type', str)
        self.columns.add('created', str)
        self.columns.add('modified', str)
        self.readonly = True


class Table_View_Files(Table_View):
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                file = self.model.datasource[index.row()]
                menu = Menu(self)
                menu_action = menu.addAction('save as...')
                def handler():
                    path = File_Dialog.getSaveFileName(self)
                menu.popup(event.globalPos())
        Table_View.mousePressEvent(self, event)


class Files(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.setWindowTitle('Files')
        self.resize(700, 700)
        self.cwidget = Widget(self)
        self.setCentralWidget(self.cwidget)

        self.tableviewfiles = Table_View_Files(self)

        layoutmain = V_Box_Layout(self.cwidget)
        layoutmain.addWidget(self.tableviewfiles)

        self.modelfiles = Model_Files()
        self.tableviewfiles.model = self.modelfiles

        from pymongo import MongoClient

        d11 = MongoClient('mongodb://comercialpicazo.com:27030')
        d11.admin.authenticate('alejandro', '47exI4')

        files = list()
        for file in d11.fedra.file.find():
            for k in list(file.keys()):
                if k not in ['name', 'id', 'type', 'file_type', 'mime_type', 'created', 'modified', 'length', 'size']:
                    del file[k]
            files.append(file)

        self.files = files
        self.modelfiles.datasource = files


if __name__ == '__main__':
    import sys
    from isis.application import Application
    app = Application(sys.argv)
    vv = Files()
    vv.show()
    sys.exit(app.exec_())
