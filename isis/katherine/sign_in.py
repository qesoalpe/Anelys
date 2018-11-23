from PySide.QtGui import *
from PySide.QtCore import *
from sarah.acp_bson import Client

class _Widget_Request_Username(QWidget):
    def __init__(self, parent, continueclick):
        QWidget.__init__(self, parent)
        self.lbl_username = QLabel('username: ', self)
        self.lbl_username.setFixedWidth(self.lbl_username.fontMetrics().width(self.lbl_username.text()))
        self.txt_username = QLineEdit(self)
        self.btn_continue = QPushButton('continue', self)
        self.mainlayout = QVBoxLayout(self)
        self.usernamelayout = QHBoxLayout()
        self.usernamelayout.addWidget(self.lbl_username)
        self.usernamelayout.addWidget(self.txt_username)
        self.mainlayout.addItem(self.usernamelayout)
        self.mainlayout.addItem(QSpacerItem(0, 500, QSizePolicy.Ignored, QSizePolicy.Ignored))
        self.mainlayout.addWidget(self.btn_continue)
        self.btn_continue.clicked.connect(continueclick)

    def showEvent(self, event):
        QWidget.showEvent(self, event)
        self.txt_username.setFocus()
        self.btn_continue.setDefault(True)

    def username(self):
        return self.txt_username.text()


class _Widget_Request_Password(QWidget):
    def __init__(self, parent, sign_in_clicked):
        QWidget.__init__(self, parent)
        self.lbl_password = QLabel('password: ', self)
        self.lbl_password.setFixedWidth(self.lbl_password.fontMetrics().width(self.lbl_password.text()))
        self.txt_password = QLineEdit(self)
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.btn_sign_in = QPushButton('sign in', self)
        self.passwordlayout = QHBoxLayout()
        self.passwordlayout.addWidget(self.lbl_password)
        self.passwordlayout.addWidget(self.txt_password)
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.addItem(self.passwordlayout)
        self.mainlayout.addItem(QSpacerItem(0, 500, QSizePolicy.Ignored, QSizePolicy.Ignored))
        self.mainlayout.addWidget(self.btn_sign_in)
        self.btn_sign_in.clicked.connect(sign_in_clicked)

    def showEvent(self, event):
        QWidget.showEvent(self, event)
        self.txt_password.setFocus()
        self.btn_sign_in.setDefault(True)

    def password(self):
        return self.txt_password.text()

class Sign_In(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.resize(300, 200)
        self.r_password_w = _Widget_Request_Password(self, self.sign_in_clicked)
        self.r_username_w = _Widget_Request_Username(self, self.continue_clicked)
        self.r_username_w.hide()
        self.r_password_w.hide()
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.addWidget(self.r_username_w)
        self.mainlayout.addWidget(self.r_password_w)
        self.request_username()
        self.agent_katherine = None

    def continue_clicked(self):
       self.request_password()

    def request_username(self):
        self.r_password_w.hide()
        self.r_username_w.show()

    def request_password(self):
        self.r_username_w.hide()
        self.r_password_w.show()

    def sign_in_clicked(self):
        if self.agent_katherine is None:
            self.agent_katherine = Client('isis.katherine.sign_in', 'katherine')
        msg = {'type_message': 'action', 'action': 'katherine/auth_user'}
        msg['username'] = self.r_username_w.username()
        msg['password'] = self.r_password_w.password()
        answer = self.agent_katherine.send_msg(msg)
        user = answer['user']
        if user is not None:
            QMessageBox.information(self, 'sign in', 'auth granted')
            self.user = user
            self.close()



import sys
app = QApplication(sys.argv)
vv = Sign_In()
vv.show()
sys.exit(app.exec_())