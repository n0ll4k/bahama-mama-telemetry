from PyQt5 import QtWidgets, uic
import sys
from bmt_db import BmtDb
from bmt_formats import BmtSensorCalibration

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('bmt.ui', self) # Load the .ui file
        self.show() # Show the GUI


def show_ui():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()


if __name__ == '__main__':
    #show_ui()
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

    db = BmtDb( r"test.db")
    db.create_tables()
    db.add_sensor( fork_sensor_dummy )
    db.add_sensor( shock_sensor_dummy )
    