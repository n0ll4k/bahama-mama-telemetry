import sqlite3
from sqlite3 import Error
from bmt_formats import BmtSensorCalibration, BmtBike, BmtSetup

class BmtDb:
    def __init__(self, path ):
        self.__db_path = path
        self.__db_conn = self.__open_connection()
    
    def __open_connection( self ):
        db_conn = None
        try:
            db_conn = sqlite3.connect( self.__db_path )
        except Error as db_err:
            print( "Error: {}".format(db_err) )
        
        return db_conn
    
    def __create_table( self, create_sql_table ):
        """
        Create a table from the create_sql_table statement
        :param create_sql_table: a CREATE TABLE statement
        :return:
        """
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( create_sql_table )
        except Error as db_err:
            print( "Error creating table: {}".format( db_err ))
    
    def close_connection( self ):
        if self.__db_conn:
            self.__db_conn.close()

    def create_tables( self ):
        """
        Create tables used for BMT evaluation.
        :param self: Pointer to object
        :return:
        """

        sql_create_bikes_table = """ CREATE TABLE IF NOT EXISTS bikes (
                                        bike_id integer PRIMARY KEY,
                                        bike_name text UNIQUE NOT NULL,
                                        travel_fork_mm integer NOT NULL,
                                        travel_shock_mm integer NOT NULL,
                                        travel_rear_mm integer NOT NULL,
                                        head_angle_degree float NOT_NULL,
                                        frame_linkage text NOT_NULL );"""

        sql_create_sensors_table = """ CREATE TABLE IF NOT EXISTS sensors (
                                        sensor_id integer PRIMARY KEY,
                                        sensor_name text UNIQUE NOT NULL,
                                        adc_value_min integer NOT NULL,
                                        adc_value_max integer NOT NULL,
                                        range_mm integer NOT NULL,
                                        flipped integer NOT NULL );"""
        
        sql_create_setups_table = """ CREATE TABLE IF NOT EXISTS setups (
                                        setup_id integer PRIMARY KEY,
                                        setup_name text UNIQUE NOT NULL,
                                        fork_sensor_id integer NOT NULL,
                                        shock_sensor_id integer NOT NULL,
                                        bike_id integer NOT NULL,
                                        FOREIGN KEY (fork_sensor_id) REFERENCES sensors (sensor_id),
                                        FOREIGN KEY (shock_sensor_id) REFERENCES sensors (sensor_id),
                                        FOREIGN KEY (bike_id) REFERENCES bikes (bike_id) );"""
        
        sql_create_sessions_table = """ CREATE TABLE IF NOT EXISTS sessions (
                                            session_id integer PRIMARY KEY,
                                            session_name text NOT NULL,
                                            session_datetime text NOT NULL,
                                            setup_id integer NOT NULL,
                                            travel_data text NOT NULL,
                                            gps_data text NOT NULL,
                                            FOREIGN KEY (setup_id) REFERENCES setups (setup_id) );"""

        if self.__db_conn is not None:
            # Create bikes table
            self.__create_table( sql_create_bikes_table )

            # Create sensors table
            self.__create_table( sql_create_sensors_table )

            # Create setups table
            self.__create_table( sql_create_setups_table )

            # Create sessions table
            self.__create_table( sql_create_sessions_table )
        else:
            print( "Error! Database connection is not established.")
    
    def add_sensor( self, sensor: BmtSensorCalibration ):
        """
        Add a new sensor to the database.
        :param self: Pointer to object
        :param sensor: Sensor object to add to sensor table
        :return: 0 on success, -1 on error
        """
        sql_add_sensor = """ INSERT INTO sensors(sensor_name, adc_value_min, adc_value_max, range_mm, flipped)
                                VALUES ( '{name}', {adc_min}, {adc_max}, {range_mm}, {flipped} );""".format(
                                    name=sensor.sensor_name(),
                                    adc_min=sensor.adc_value_zero(),
                                    adc_max=sensor.adc_value_max(),
                                    range_mm=sensor.range_mm(),
                                    flipped=int(sensor.flip_travel()) )
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_add_sensor )
            self.__db_conn.commit()
        except Error as db_err:
            return ( -1, f"Error creating sensor: {db_err}" )
        return ( 0, "")
    
    def add_bike( self, bike: BmtBike ):
        """
        Add a new bike to the database.
        :param self: Pointer to object
        :param bike: Bike object to add to bike table
        :return: 0 on success, -1 on error
        """
        sql_add_bike = """ INSERT INTO bikes(bike_name, travel_fork_mm, travel_shock_mm, travel_rear_mm, head_angle_degree, frame_linkage)
                            VALUES ( '{name}', {travel_fork}, {travel_shock}, {travel_rear}, {head_angle}, '{linkage_file}' );""".format(
                                name=bike.bike_name(),
                                travel_fork=bike.travel_fork_mm(),
                                travel_shock=bike.travel_shock_mm(),
                                travel_rear=bike.travel_rear_axle_mm(),
                                head_angle=bike.head_angle(),
                                linkage_file=bike.frame_linkage() )
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_add_bike )
            self.__db_conn.commit()
        except Error as db_err:
            return ( -1, f"Error creating bike: {db_err}" )
        return ( 0, "")
    
    def add_session( self, session_name, session_datetime, setup_id, travel_data, gps_data ):
        """
        Add a new bike to the database.
        :param self: Pointer to object
        :param session_name: name of the session to save
        :param session_datetime: Date and Time of session
        :param setup_id: setup_id of session
        :param travel_data: Path to travel data file
        :param gps_data: Path to GPS data file
        :return: 0 on success, -1 on error
        """
        sql_add_session = f"""INSERT INTO sessions(session_name, session_datetime, setup_id, travel_data, gps_data)
                            VALUES ( '{session_name}', '{session_datetime}', {setup_id}, '{travel_data}', '{gps_data}' );"""
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql_add_session)
            self.__db_conn.commit()
        except Error as db_err:
            return ( -1, f"Error creating bike: {db_err}" )
        return ( 0, "")

    def get_sensor_list( self ):
        """
        Read a sensor list from the database.
        :param self: Pointer to object
        :return: Tuple: (list(), err_msg)
        """
        sql_get_sensors = """SELECT sensor_id, sensor_name from sensors
                             ORDER BY sensor_id;"""

        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_get_sensors )
            rows = cursor.fetchall()
        except Error as db_err:
            return ( list(), f"Error reading sensor list: {db_err}")
        
        return ( rows, "" )
    
    def get_bike_list( self ):
        """
        Read a bike list from the database.
        :param self: Pointer to object
        :return: Tuple: (list(), err_msg)
        """
        sql_get_sensors = """SELECT bike_id, bike_name from bikes
                             ORDER BY bike_id;"""

        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_get_sensors )
            rows = cursor.fetchall()
        except Error as db_err:
            return ( list(), f"Error reading sensor list: {db_err}")
        
        return ( rows, "" )

    def add_setup(self, name, bike_id, fork_id, shock_id ):
        """
        Add a setup to the db.
        :param self: Pointer to object
        :param bike_id: bike_id from bikes
        :param front_id: sensor_id from sensors
        :param read_id: sensor_id from sensors
        :return: 0 on success, -1 on error
        """
        sql_add_setup = f""" INSERT INTO setups(setup_name, fork_sensor_id, shock_sensor_id, bike_id)
                            VALUES ( '{name}', {fork_id}, {shock_id}, {bike_id} );"""
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_add_setup )
            self.__db_conn.commit()
        except Error as db_err:
            return ( -1, f"Error creating bike: {db_err}" )
        return ( 0, "")

    def get_setup_list(self):
        """
        Read a setup list from the database.
        :param self: Pointer to object
        :return: Tuple: (list(), err_msg)
        """
        sql_get_sensors = """SELECT setup_id, setup_name from setups
                             ORDER BY setup_id;"""

        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_get_sensors )
            rows = cursor.fetchall()
        except Error as db_err:
            return ( list(), f"Error reading sensor list: {db_err}")
        
        return ( rows, "" )
    
    def get_setup(self, setup_id):
        """
        Read the setup data of a specific id.
        :param self: Pointer to object
        :para setup_id: Database id of setup
        :return: On Error: None, On Success: Tuple( bike_id, front_sensor_id, rear_sensor_id)
        """
        sql_get_setup = f"""SELECT setup_name, bike_id, fork_sensor_id, shock_sensor_id from setups 
                        WHERE setup_id={setup_id}"""
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql_get_setup)
            rows = cursor.fetchone()
        except Error as db_err:
            return ( None, f"Error reading setup: {db_err}")

        setup = BmtSetup()
        setup.set_setup_id(setup_id)
        setup.set_setup_name(rows[0])
        # Get Bike object.
        bike = self.get_bike(rows[1])
        if bike[0] is None:
            return (None, bike[1])
        # Get Front sensor object.
        front_sensor = self.get_sensor(rows[2])
        if front_sensor[0] is None:
            return (None, front_sensor[1])
        # Get Rear sensor object.
        rear_sensor = self.get_sensor(rows[3])
        if rear_sensor[0] is None:
            return (None, rear_sensor[1])
        
        setup.set_bike(bike[0])
        setup.set_fork_sensor(front_sensor[0])
        setup.set_shock_sensor(rear_sensor[0])
        return ( setup, "" )

    def get_bike(self, bike_id):
        """
        Read the bike data of a specific id.
        :param self: Pointer to object
        :para bike_id: Database id of setup
        :return: On Error: None, On Success: BmtBike Object
        """
        sql_get_bike = f"""SELECT bike_name, travel_fork_mm, travel_shock_mm, travel_rear_mm, head_angle_degree, frame_linkage from bikes
                        WHERE bike_id={bike_id}"""
        
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql_get_bike)
            rows = cursor.fetchone()
        except Error as db_err:
            return ( None, f"Error reading bike: {db_err}")

        bike = BmtBike()
        bike.set_bike_name(rows[0])
        bike.set_travel_fork_mm(rows[1])
        bike.set_travel_shock_mm(rows[2])
        bike.set_travel_rear_axle_mm(rows[3])
        bike.set_head_angle(rows[4])
        bike.set_frame_linkage(rows[5])

        return ( bike, "" )

    def get_sensor(self, sensor_id):
        """
        Read the setup data of a specific id.
        :param self: Pointer to object
        :para sensor_id: Database id of sensor
        :return: On Error: None, On Success: BmtSensorCalibration Object
        """
        sql_get_sensor = f"""SELECT  sensor_name, adc_value_min, adc_value_max, range_mm, flipped FROM sensors
                        WHERE sensor_id={sensor_id}"""
        
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql_get_sensor)
            rows = cursor.fetchone()
        except Error as db_err:
            return ( None, f"Error reading sensor: {db_err}")

        sensor = BmtSensorCalibration()
        sensor.set_sensor_id(sensor_id)
        sensor.set_sensor_name(rows[0])
        sensor.set_adc_value_zero(rows[1])
        sensor.set_adc_value_max(rows[2])
        sensor.set_range_mm(rows[3])
        sensor.set_flip_travel(bool(rows[4]))

        return ( sensor, "" )

    def get_session_list(self):
        """
        Read a session list from the database.
        :param self: Pointer to object
        :return: Tuple: (list(), err_msg)
        """
        sql_get_sessions = """SELECT session_id, session_name from sessions
                             ORDER BY session_id;"""

        try:
            cursor = self.__db_conn.cursor()
            cursor.execute( sql_get_sessions )
            rows = cursor.fetchall()
        except Error as db_err:
            return ( list(), f"Error reading sensor list: {db_err}")
        
        return ( rows, "" )

    def get_session_data(self, session_id):
        """
        Read the session data of a specific id.
        :param self: Pointer to object
        :para session_id: Database id of session.
        :return: On Error: None, On Success: Tuple( travel_csv_path, gps_csv_path)
        """
        sql_get_session_data = f"""SELECT  travel_data, gps_data FROM sessions
                                WHERE session_id={session_id}"""
        
        try:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql_get_session_data)
            rows = cursor.fetchone()
        except Error as db_err:
            return ( None, f"Error reading sensor: {db_err}")
        
        return rows
