from isis.dialog import Dialog
from isis.widget import Widget




class Filter(Dialog):
    def __init__(self, *args, **kwargs):
        Dialog.__init__(self, *args, **kwargs)
        self.resize(600, 600)

if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    d = Filter()
    d.show()
    sys.exit(app.exec_())
