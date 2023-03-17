# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QFileDialog, QErrorMessage
# PyQt uic
from PyQt5 import uic
# JSON
import json
# Sensor Calibration format
from bmt_formats import BmtSensorCalibration

class AddSensorUi(QWidget):
    def __init__(self, parent, db):
        QWidget.__init__(self)
        self.Parent = parent
        self.db = db
        uic.loadUi('ui_files/add_sensor.ui', self)
        
        # Link buttons to callback functions
        self.load_json_bttn.clicked.connect(self.load_json_cb)
        self.save_bttn.clicked.connect(self.save_data)

    def closeEvent(self, event):
        self.Parent.add_sensor_open = False
        self.close()

    def save_data(self):
        sensor = BmtSensorCalibration()
        sensor.set_sensor_name(self.sensor_name.text())
        if sensor.sensor_name() == "":
            error = "Please set a name."
            print( error )
            error_dialog = QErrorMessage()
            error_dialog.showMessage(error)
            return
        sensor.set_adc_value_zero(self.adcMin_val.value())
        sensor.set_adc_value_max(self.adcMax_val.value())
        if ( sensor.adc_value_max() == sensor.adc_value_zero()):
            error = "Please set different min and max values."
            print( error )
            error_dialog = QErrorMessage()
            error_dialog.showMessage(error)
            return
        sensor.set_range_mm( self.range_val.value() )
        if sensor.range_mm() <= 0:
            error = "Please set a sensor range larger 0mm."
            print( error )
            error_dialog = QErrorMessage()
            error_dialog.showMessage(error)
            return
        sensor.set_flip_travel( self.flip_travel_check.isChecked())
        self.db.add_sensor( sensor)
        self.close()
        


    def load_json_cb(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Open Sensor JSON File", 
                                               "JSON Files (*.json)")
        print(filename)
        sensor_data = self.load_json_file( filename[0])
        if sensor_data == None:
            error_dialog = QErrorMessage()
            error_dialog.showMessage(f"Please select a correct json file.")
        else:
            try:
                print( sensor_data )
                self.sensor_name.setText(sensor_data['sensor_name'])
                self.adcMin_val.setValue(sensor_data['adc_val_zero'])
                self.adcMax_val.setValue(sensor_data['adc_val_max'])
                self.range_val.setValue(sensor_data['range_mm'])
                self.flip_travel_check.setChecked(sensor_data['flip_travel'])
            except KeyError as errk:
                error_dialog = QErrorMessage()
                error_dialog.showMessage(f"Please select a correct json file.\n{errk}")

    def load_json_file(self, filename):
        try:
            with open (filename) as file:
                json_data = json.load(file)
            file.close()
            return json_data
        except json.decoder.JSONDecodeError as errj:
            error_dialog = QErrorMessage()
            error_dialog.showMessage(f"Please select a correct json file.\n{errj}")
        except FileNotFoundError as errf:
            error_dialog = QErrorMessage()
            error_dialog.showMessage(f"Please select a correct json file.\n{errf}")


        


