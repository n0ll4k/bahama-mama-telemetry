# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QMessageBox
# PyQt uic
from PyQt5 import uic
# Setup format
from bmt_formats import BmtSetup

class AddSetup(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.Parent = parent
        uic.loadUi('ui_files/create_setup.ui', self)

        self.sensor_list = self.Parent.db.get_sensor_list()[0]
        self.bike_list = self.Parent.db.get_bike_list()[0]

        # Link buttons to callback functions
        self.save_bttn.clicked.connect(self.save_data)

        # Fill lists
        self.fill_lists()

    def closeEvent(self, event):
        self.Parent.create_setup_open = False
        self.close()
    
    def save_data(self):
        bike = self.bike_list_1.currentItem().text()
        front_sensor = self.sensor_list_1.currentItem().text()
        rear_sensor = self.sensor_list_2.currentItem().text()
        

        bike_id = self.get_bike_id_by_name(bike)
        front_sensor_id = self.get_sensor_id_by_name(front_sensor)
        rear_sensor_id = self.get_sensor_id_by_name(rear_sensor)
        if front_sensor_id == rear_sensor_id:
            self.show_error("Please select 2 different sensors.")
            return
        if self.setup_name.text() == "":
            self.show_error("Please set a setup name.")
            return
        return_value = self.Parent.db.add_setup(self.setup_name.text(), 
                                                bike_id, 
                                                front_sensor_id, 
                                                rear_sensor_id)
        if return_value[0] == -1:
            self.show_error( return_value[1] )
            return
        self.close()

    def fill_lists(self):
        # Create bike name list.
        bike_names = list()
        for bike in self.bike_list:
            bike_names.append(bike[1])

        # Create sensor name list.
        sensor_names = list()
        for sensor in self.sensor_list:
            sensor_names.append(sensor[1])

        # Fill listWidgets
        self.bike_list_1.addItems(bike_names)
        self.sensor_list_1.addItems(sensor_names)
        self.sensor_list_2.addItems(sensor_names)

    def get_bike_id_by_name(self, name):
        for item in self.bike_list:
            if item[1] == name:
                return item[0]
        return None
    
    def get_sensor_id_by_name(self, name):
        for item in self.sensor_list:
            if item[1] == name:
                return item[0]
        return None
    
    def show_error( self, message ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()



        