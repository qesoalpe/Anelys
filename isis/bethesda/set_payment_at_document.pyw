from PySide.QtCore import *
from PySide.QtGui import *

class Set_Payment_At_Document(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle('Set_Payment_At_Document')
        self.resize(200, 500)


        lbl_document = QLabel('document', self)
        lbl_document_id = QLabel('id: ', self)
        lbl_document_folio = QLabel('folio: ', self)
        lbl_document_value = QLabel('value: ', self)
        lbl_document_datetime = QLabel('datetime: ', self)





if __name__ == '__main__':
    import sys
    from PySide.QtGui import QApplication
    app = QApplication(sys.argv)
    vv = Set_Payment_At_Document()
    vv.show()
    sys.exit(app.exec_())
