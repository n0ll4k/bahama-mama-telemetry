# QWidgets Container Objects
from PyQt5.QtWidgets import QMainWindow, QWidget
# PyQt uic
from PyQt5 import uic

class AddSensorUi(QWidget):
    def __init__(self, parent, db):
        QWidget.__init__(self)
        self.Parent = parent
        self.db = db
        uic.loadUi('ui_files/add_sensor.ui', self)

    def closeEvent(self, event):
        self.Parent.add_sensor_open = False
        self.close()