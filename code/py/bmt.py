from PyQt5 import QtWidgets, uic
import sys
from bmt_db import BmtDb
from bmt_formats import BmtSensorCalibration, BmtBike
from bmt_add_sensor import AddSensorUi
from bmt_add_bike import AddBikeUi

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('ui_files/bmt.ui', self) # Load the .ui file
        self.add_sensor_open = False
        self.add_bike_open = False

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
            self.AddBike = AddBikeUi(self, self.db)
            self.AddBike.show()

    def addSensor_cb(self):
        if not self.add_sensor_open:
            self.add_sensor_open = True
            self.AddSensor = AddSensorUi(self, self.db)
            self.AddSensor.show()

    def oldSession_cb(self):
        print( "Load old Session.")

    def newSession_cb(self):
        print( "Create new Session.")
    
    def newSetup_cb(self):
        print( "Create new Setup.")

def show_ui():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()




if __name__ == '__main__':
    show_ui()
    '''
    fork_sensor_dummy = BmtSensorCalibration()
    fork_sensor_dummy.set_sensor_name( "Fork Dummy")
    fork_sensor_dummy.set_adc_value_zero( 25 ) 
    fork_sensor_dummy.set_adc_value_max( 4095 )
    fork_sensor_dummy.set_range_mm( 200 )
    fork_sensor_dummy.set_flip_travel(True)

    shock_sensor_dummy = BmtSensorCalibration()
    shock_sensor_dummy.set_sensor_name( "Shock Dummy")
    shock_sensor_dummy.set_adc_value_zero( 22 ) 
    shock_sensor_dummy.set_adc_value_max( 4095 )
    shock_sensor_dummy.set_range_mm( 75 )
    shock_sensor_dummy.set_flip_travel(False)

    dummy_bike = BmtBike()
    dummy_bike.set_bike_name( "Kavenz VHP16 Fred")
    dummy_bike.set_head_angle( 64.0 )
    dummy_bike.set_travel_rear_mm(160)
    dummy_bike.set_travel_fork_mm(170)
    dummy_bike.set_travel_shock_mm(65)
    dummy_bike.set_frame_linkage("/Users/n0ll4k/Documents/bmt_data/travel_data/Kavenz_VHP16.json")

    db = BmtDb( r"test.db")
    db.create_tables()
    db.add_sensor( fork_sensor_dummy )
    db.add_sensor( shock_sensor_dummy )
    db.add_bike( dummy_bike )
    '''