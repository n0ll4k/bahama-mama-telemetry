# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
# PyQt uic
from PyQt5 import uic
# JSON
import json
# Sensor Calibration format
from bmt_formats import BmtSensorCalibration

class AddSensorUi(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.Parent = parent
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
            self.show_error("Please set a name.")
            return
        sensor.set_adc_value_zero(self.adcMin_val.value())
        sensor.set_adc_value_max(self.adcMax_val.value())
        if ( sensor.adc_value_max() == sensor.adc_value_zero()):
            self.show_error("Please set different min and max values.")
            return
        sensor.set_range_mm( self.range_val.value() )
        if sensor.range_mm() <= 0:
            self.show_error("Please set a sensor range larger 0mm.")
            return
        sensor.set_flip_travel( self.flip_travel_check.isChecked())
        return_value = self.Parent.db.add_sensor( sensor)
        if return_value[0] == -1:
            self.show_error( return_value[1] )
            return
        self.close()
        


    def load_json_cb(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Open Sensor JSON File", 
                                               "JSON Files (*.json)")
        sensor_data = self.load_json_file( filename[0])
        if sensor_data is not None:
            try:    
                self.sensor_name.setText(sensor_data['sensor_name'])
                self.adcMin_val.setValue(sensor_data['adc_val_zero'])
                self.adcMax_val.setValue(sensor_data['adc_val_max'])
                self.range_val.setValue(sensor_data['range_mm'])
                self.flip_travel_check.setChecked(sensor_data['flip_travel'])
            except KeyError as errk:
                self.show_error(f"Please select a correct json file.\n{errk}" )


    def load_json_file(self, filename):
        try:
            with open (filename) as file:
                json_data = json.load(file)
            file.close()
            return json_data
        except json.decoder.JSONDecodeError as errj:
            self.show_error(f"Please select a correct json file.\n{errj}" )
        except FileNotFoundError as errf:
            self.show_error(f"Please select a correct json file.\n{errf}" )

    def show_error( self, message ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()


        


