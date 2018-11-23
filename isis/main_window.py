from PySide2.QtWidgets import QMainWindow

pool_mainwindow = list()


class Main_Window(QMainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        self._persist = True
        pool_mainwindow.append(self)


    @property
    def central_widget(self):
        return self.centralWidget()

    @central_widget.setter
    def central_widget(self, value):
        self.setCentralWidget(value)

    cwidget = central_widget

    @property
    def persist(self):
        return self._persist

    @persist.setter
    def persist(self, persist):
        self._persist = persist
        if persist:
            pool_mainwindow.append(self)
        else:
            if self in pool_mainwindow:
                pool_mainwindow.remove(self)

