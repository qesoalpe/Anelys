from isis.main_window import Main_Window
from isis.widget import Widget
from isis.valentine.widget_viewer_storage import Widget_Viewer_Storage
from isis.v_box_layout import V_Box_Layout
from isis.valentine.manage_items_supply.main_window import Widget as Manage_Items_Supply_Widget

from PySide2.QtWidgets import QMdiArea


class Manage(Main_Window):
    def __init__(self):
        Main_Window.__init__(self)
        self.resize(600, 500)
        self.cwidget = Widget(self)

        self.viewerstorage = Widget_Viewer_Storage(self.cwidget)
        self.workspace = QMdiArea(self.cwidget)
        # self.tabwidget = Tab_Widget(self.cwidget)
        # self.tabwidget.addTab(self.manage_items_supply, 'Manage items supply')

        self.viewerstorage.with_button_change = True

        self.manage_items_supply = Manage_Items_Supply_Widget(self.cwidget)
        self.manage_items_supply.setWindowTitle('MMM')
        self.workspace.addSubWindow(self.manage_items_supply)

        layout_main = V_Box_Layout(self.cwidget)

        layout_main.addWidget(self.viewerstorage)
        layout_main.addWidget(self.workspace)

        self.cwidget.layout = layout_main

        self.manage_items_supply.manage_items_supply = '226-2'


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    mw = Manage()
    mw.show()
    sys.exit(app.exec_())
