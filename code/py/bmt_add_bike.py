# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
# PyQt uic
from PyQt5 import uic
# JSON
import json
# Sensor Calibration format
from bmt_formats import BmtBike
# os.path
import os.path as path

class AddBikeUi(QWidget):
    def __init__(self, parent, db):
        QWidget.__init__(self)
        self.Parent = parent
        self.db = db
        uic.loadUi('ui_files/add_bike.ui', self)

        # Link buttons to callback functions
        self.load_json_bttn.clicked.connect(self.load_bike_json_cb)
        self.sel_linkage_bttn.clicked.connect(self.load_bike_linkage_cb)
        self.save_bttn.clicked.connect(self.save_data)

    def closeEvent(self, event):
        self.Parent.add_bike_open = False
        self.close()

    def save_data(self):
        print( "Saving data")
        bike = BmtBike()
        bike.set_bike_name(self.bike_name.text())
        if bike.bike_name() == "":
            self.show_error("Please set a name.")
            return
        bike.set_travel_fork_mm(self.fork_travel.value())
        if bike.travel_fork_mm() <= 10:
            self.show_error("Please set a correct fork travel.")
            return
        bike.set_travel_shock_mm(self.shock_travel.value())
        if bike.travel_fork_mm() <= 10:
            self.show_error("Please set a correct shock travel.")
            return
        bike.set_travel_rear_axle_mm(self.frame_travel.value())
        if bike.travel_rear_axle_mm() <= 10:
            self.show_error("Please set a correct frame travel.")
            return
        bike.set_head_angle(self.head_angle.value())
        if bike.head_angle() < 50.0 or bike.head_angle() > 80:
            self.show_error("Please set a correct head angle.")
            return
        bike.set_frame_linkage(self.linkage_path.text())
        if not path.isfile(bike.frame_linkage()):
            self.show_error("Please set a valid linkage file path.")
            return
        return_value = self.db.add_bike( bike )
        if return_value[0] == -1:
            self.show_error( return_value[1] )
            return
        self.close()
    
    def load_bike_json_cb(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Open Bike JSON File", 
                                               "JSON Files (*.json)")
        bike_data = self.load_json_file( filename[0])
        if bike_data is not None:
            try:
                self.bike_name.setText(bike_data['bike_name'])
                self.fork_travel.setValue(bike_data['travel_fork_mm'])
                self.shock_travel.setValue(bike_data['travel_shock_mm'])
                self.frame_travel.setValue(bike_data['travel_rear_axle_mm'])
                self.head_angle.setValue(bike_data['head_angle'])
                self.linkage_path.setText(bike_data['frame_linkage'])                
            except KeyError as errk:
                self.show_error(f"Please select a correct json file.\n{errk}")

    def load_bike_linkage_cb(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Open Linkage JSON File", 
                                               "JSON Files (*.json)")
        try:
            # Load file just for verification
            linkage_data = self.load_json_file(filename[0])
            if linkage_data is not None:
                self.linkage_path.setText(filename[0])
            
            
        except:
            self.show_error(f"Please select a correct json file.\n")

    def load_json_file(self, filename):
        try:
            with open (filename) as file:
                json_data = json.load(file)
            file.close()
            return json_data
        except json.decoder.JSONDecodeError as errj:
            self.show_error(f"Please select a correct json file.\n{errj}")
        except FileNotFoundError as errf:
            self.show_error(f"Please select a correct json file.\n{errf}")
    
    def show_error( self, message ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()