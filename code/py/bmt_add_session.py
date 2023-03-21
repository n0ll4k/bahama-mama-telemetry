# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
# PyQt uic
from PyQt5 import uic
# QDateTime
from PyQt5.QtCore import QDateTime
# os.path
import os.path as path
# Data parser
from bmt_read_file import BmtLogReader
# Visualization
from bmt_visualization import BmtVisualization


class AddSessionUi(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.Parent = parent
        self.setup_list = list()
        uic.loadUi('ui_files/add_session.ui', self)

        # Link buttons to callback functions
        self.select_data_bttn.clicked.connect(self.select_data_cb)
        self.proc_save_bttn.clicked.connect(self.proc_save_cb)

        # Set current datetime.
        self.date_time.setDateTime(QDateTime.currentDateTime())

        # Fill setup list
        self.setup_list = self.Parent.db.get_setup_list()[0]
        self.setup_names = list()
        for setup in self.setup_list:
            self.setup_names.append(setup[1])
        self.setup_list_widget.addItems(self.setup_names)


    def closeEvent(self, event):
        self.Parent.add_session_open = False
        self.close()

    def proc_save_cb(self):
        session_name = self.build_session_name()
        # Check if data file is selected.
        if not path.isfile(self.data_file.text()):
            self.show_error( "Please select a valid data file.")
        # Get Setup from database.
        setup_name = self.setup_list_widget.currentItem().text()
        setup = self.Parent.db.get_setup(self.get_setup_id_by_name(setup_name))
        if setup[0] is None:
            self.show_error( setup[1])
        # Read Data.
        data_paths = BmtLogReader.process_data( self.data_file.text(), setup[0] )
        print(data_paths)
        
        # TODO Add data/filepaths to database.
        return_value = self.Parent.db.add_session(session_name, 
                                                  self.date_time.dateTime().toString("dd.MM.yyyy HH:mm:ss"), 
                                                  self.get_setup_id_by_name(setup_name), 
                                                  data_paths[0],
                                                  data_paths[1] )
        if return_value[0] != 0:
            self.show_error(return_value[1])
            return
        else:
            travel_df = BmtVisualization.open_travel_information( data_paths[0] )
            gps_df = BmtVisualization.open_gps_information( data_paths[1])
    
            export_file = "{}.html".format( path.basename(data_paths[1])[:-7])
            export = path.abspath( path.join(path.dirname(data_paths[1]), export_file ))

            BmtVisualization.present_data( travel_df, gps_df, export )
            self.close()
            

    def select_data_cb(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Open raw data file.", 
                                               "Log Files (*.log)")
        if not path.isfile(filename[0]):
            self.show_error("Please select a valid file.")
            return
        else:
            self.data_file.setText(filename[0])
    
    def get_setup_id_by_name(self, name):
        for item in self.setup_list:
            if item[1] == name:
                return item[0]
        return None

    def build_session_name(self):
        session_time = self.date_time.dateTime().toString("dd.MM.yyyy HH:mm:ss")
        setup_name = self.setup_list_widget.currentItem().text()
        return f"{setup_name} {session_time}"
        
    def show_error( self, message ):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()