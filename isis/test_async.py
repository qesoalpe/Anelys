from isis.dialog import Dialog
from isis.push_button import Push_Button
from isis.line_edit import Line_Edit
from isis.label import Label
from isis.message_box import Message_Box
from isis.v_box_layout import V_Box_Layout
from isis.h_box_layout import H_Box_Layout
import threading
import time
from datetime import datetime
from isodate import datetime_isoformat


class Text_Async(Dialog):
    def __init__(self):
        Dialog.__init__(self)
        self.btn = Push_Button('Press me', self)
        self.btn_2 = Push_Button('also press to me', self)
        self.txt = Line_Edit(self)
        self.lbl = Label(self)

        self.btn.clicked.connect(self.handle_it)

        layout_main = V_Box_Layout(self)
        layout_main.addWidget(self.txt)
        layout_main.addWidget(self.lbl)

        buttons_layout = H_Box_Layout()
        buttons_layout.addWidget(self.btn)
        buttons_layout.addWidget(self.btn_2)
        layout_main.addLayout(buttons_layout)
        self.layout = layout_main

    def handle_it(self):
        def hh():
            time.sleep(3)
            self.lbl.text = datetime_isoformat(datetime.now())

        t = threading.Thread(target=hh)
        t.start()


if __name__ == '__main__':
    from isis.application import Application
    import sys
    app = Application(sys.argv)
    d = Text_Async()
    d.show()
    sys.exit(app.exec_())
