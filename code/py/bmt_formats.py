DATA_HEADER_POS_TYPE = 0
DATA_HEADER_POS_RES = 1
DATA_HEADER_POS_LENGTH = 2

GPS_SENTENCES = ['$GPGGA', '$GPVTG', '$GPRMC']

DATA_HEADER_FMT = '<cBH'
# [0]: uint8    - Data type
# [1]: uint8    - Reserved
# [2]: uint16   - Data length

TIMESTAMP_FMT = '<L'
# [0]: uint32   - timestamp

TRAVEL_INFORMATION_FMT = '<HH'
# [0]: uint16   - Fork ADC data
# [1]: uint16   - Shock ADC data

class BmtSensorCalibration:
    def __init__( self ):
        self._sensor_id = 0
        self._sensor_name = ""
        self._adc_value_zero = 0
        self._adc_value_max = 0
        self._range_mm = 0
        self._flip_travel = False
    
    def set_sensor_id( self, sensor_id ):
        self._sensor_id = sensor_id
    
    def set_sensor_name( self, sensor_name ):
        self._sensor_name = sensor_name
    
    def set_adc_value_zero( self, adc_val_zero ):
        self._adc_value_zero = adc_val_zero

    def set_adc_value_max( self, adc_val_max ):
        self._adc_value_max = adc_val_max

    def set_range_mm( self, range_mm ):
        self._range_mm = range_mm

    def set_flip_travel( self, flip_travel ):
        self._flip_travel = flip_travel

    def sensor_id( self ):
        return self._sensor_id

    def sensor_name( self ):
        return self._sensor_name

    def adc_value_zero( self ):
        return self._adc_value_zero

    def adc_value_max( self ):
        return self._adc_value_max

    def range_mm( self ):
        return self._range_mm
    
    def flip_travel( self ):
        return self._flip_travel
    
class BmtBike:
    def __init__( self ):
        self._bike_id = 0
        self._bike_name = ""
        self._travel_fork_mm = 0
        self._travel_rear_mm = 0
        self._head_angle = 0.0
        self._frame_linkage = ""
    
    def set_bike_id( self, bike_id ):
        self._bike_id = bike_id

    def set_bike_name( self, bike_name ):
        self.set_bike_name = bike_name
    
    def set_travel_fork_mm( self, travel_fork_mm ):
        self._travel_fork_mm = travel_fork_mm

    def set_travel_rear_mm( self, travel_rear_mm ):
        self._travel_read_mm = travel_rear_mm
    
    def set_head_angle( self, head_angle ):
        self._head_angle = head_angle
    
    def set_frame_linkage( self, linkage_data ):
        self._frame_linkage = linkage_data

    def bike_id( self ):
        return self._bike_id
    
    def bike_name( self ):
        return self._bike_name

    def travel_fork_mm( self ):
        return self._travel_fork_mm
    
    def travel_rear_mm( self ):
        return self._travel_rear_mm
    
    def head_angle( self ):
        return self._head_angle
    
    def frame_linkage( self ):
        return self._frame_linkage

class BmtSetup:
    def __init__( self ):
        self._setup_id = 0
        self._fork_sensor = BmtSensorCalibration()
        self._shock_sensor = BmtSensorCalibration()
        self._bike = BmtBike()
    
    def set_fork_sensor( self, fork_sensor ):
        self._fork_sensor = fork_sensor
    
    def set_shock_sensor( self, shock_sensor ):
        self._shock_sensor = shock_sensor

    def set_bike( self, bike ):
        self._bike = bike

    def fork_sensor( self ):
        return self._fork_sensor
    
    def shock_sensor( self ):
        return self._shock_sensor
    
    def bike( self ):
        return self._bike

    

