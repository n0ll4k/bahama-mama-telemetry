from PyQt5 import QtWidgets, uic
import sys
from bmt_db import BmtDb
from bmt_formats import BmtSensorCalibration, BmtBike
from bmt_add_sensor import AddSensorUi
from bmt_add_bike import AddBikeUi
from bmt_add_setup import AddSetup
from bmt_add_session import AddSessionUi
from bmt_old_session import OldSessionUi

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('ui_files/bmt.ui', self) # Load the .ui file
        self.add_sensor_open = False
        self.add_bike_open = False
        self.create_setup_open = False
        self.add_session_open = False
        self.old_session_open = False

        # Link Buttons to callback functions.
        self.addBike_bttn.clicked.connect(self.addBike_cb)
        self.addSensor_bttn.clicked.connect(self.addSensor_cb)
        self.newSetup_bttn.clicked.connect(self.newSetup_cb)
        self.newSession_bttn.clicked.connect(self.newSession_cb)
        self.oldSession_bttn.clicked.connect(self.oldSession_cb)

        # Create database connection.
        self.db = BmtDb( r"test.db")
        self.db.create_tables()

        self.show() # Show the GUI

    def addBike_cb(self):
        if not self.add_bike_open:
            self.add_bike_open = True
            self.AddBike = AddBikeUi(self)
            self.AddBike.show()

    def addSensor_cb(self):
        if not self.add_sensor_open:
            self.add_sensor_open = True
            self.AddSensor = AddSensorUi(self)
            self.AddSensor.show()

    def oldSession_cb(self):
        if not self.old_session_open:
            self.old_session_open = True
            self.OldSession = OldSessionUi(self)
            self.OldSession.show()

    def newSession_cb(self):
        if not self.add_session_open:
            self.add_session_open = True
            self.AddSession = AddSessionUi(self)
            self.AddSession.show()
    
    def newSetup_cb(self):
        if not self.create_setup_open:
            self.create_setup_open = True
            self.AddSetup = AddSetup(self)
            self.AddSetup.show()
        

def show_ui():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()




if __name__ == '__main__':
    show_ui()