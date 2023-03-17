import sqlite3
from sqlite3 import Error
from bmt_formats import BmtSensorCalibration, BmtBike

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

        