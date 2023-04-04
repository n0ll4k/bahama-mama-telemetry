# QWidgets Container Objects
from PyQt5.QtWidgets import QWidget, QMessageBox
# PyQt uic
from PyQt5 import uic
# os.path
import os.path as path
# Visualization
from bmt_visualization import BmtVisualization

class OldSessionUi(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.Parent = parent
        uic.loadUi('ui_files/old_session.ui', self)

        self.sessions = self.Parent.db.get_session_list()[0]

        # Link buttons to callback functions
        self.show_session_bttn.clicked.connect(self.show_session)

        # Create session name list.
        session_names = list()
        for session in self.sessions:
            session_names.append(session[1])

        # Fill listWidgets
        self.session_list.addItems(session_names)

    def closeEvent(self, event):
        self.Parent.old_session_open = False
        self.close()
    
    def show_session(self):
        session_id = self.get_setup_id_by_name(self.session_list.currentItem().text())
        data_paths = self.Parent.db.get_session_data(session_id)

        travel_df = BmtVisualization.open_travel_information( data_paths[0] )
        gps_df = BmtVisualization.open_gps_information( data_paths[1])

        export_file = "{}.html".format( path.basename(data_paths[1])[:-7])
        export = path.abspath( path.join(path.dirname(data_paths[1]), export_file ))

        BmtVisualization.present_data( travel_df, gps_df, export )
        self.close()

    def get_setup_id_by_name(self, name):
        for item in self.sessions:
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



        