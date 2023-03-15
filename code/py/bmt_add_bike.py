# QWidgets Container Objects
from PyQt5.QtWidgets import QMainWindow, QWidget
# PyQt uic
from PyQt5 import uic

class AddBikeUi(QWidget):
    def __init__(self, parent, db):
        QWidget.__init__(self)
        self.Parent = parent
        self.db = db
        uic.loadUi('ui_files/add_bike.ui', self)

    def closeEvent(self, event):
        self.Parent.add_bike_open = False
        self.close()