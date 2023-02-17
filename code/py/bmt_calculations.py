import math
import pandas as pd
from pyproj import Transformer
from bmt_formats import BmtSetup, BmtBike, BmtSensorCalibration

lonlat_to_webmercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

class BmtCalculationsAdc2Mm:
    def __init__( self, sensor_info: BmtSensorCalibration ):
        self._gradient = sensor_info.range_mm() / ( sensor_info.adc_value_max()-sensor_info.adc_value_zero())
        self._offset = sensor_info.range_mm() - ( (sensor_info.range_mm()*sensor_info.adc_value_max()) / ( sensor_info.adc_value_max()-sensor_info.adc_value_zero()) )
    
    def adc2mm( self, adc_val ):
        mm_val = adc_val * self._gradient + self._offset
        return round(mm_val, 1 )

class BmtCalculations:
    @staticmethod
    def rad2dec( input, direction):
        try:
            deg = float(int( input / 100 )) 
        except:
            return( 0.0 )
        decimal =  deg + (( input - (deg * 100 )) / 60 )
        if direction in ['W', 'S']:
            decimal *= -1

        return( decimal )
    
    @staticmethod
    def lat_lon2x_y(lat, lon):
        x, y = lonlat_to_webmercator.transform(lon, lat)
        return [x, y]

    @staticmethod
    def adc_to_mm( input_df : pd.DataFrame, calibration_data: BmtSensorCalibration, column_name: str ):
        calculator = BmtCalculationsAdc2Mm( calibration_data )

        input_df[column_name] = input_df.apply( lambda row: calculator.adc2mm(row.fork_adc), axis=1)
        
        return input_df
    
    @staticmethod
    def transform_gps_data( gps_df: pd.DataFrame ):
        gps_df['lat_dec'] = gps_df.apply( lambda row: BmtCalculations.rad2dec( row.lat, row.lat_dir ), axis=1)
        gps_df['lon_dec'] = gps_df.apply( lambda row: BmtCalculations.rad2dec( row.lon, row.lon_dir ), axis=1)
        gps_df[['x', 'y']] = gps_df.apply( lambda row: BmtCalculations.lat_lon2x_y( row.lat_dec, row.lon_dec ), axis=1, result_type='expand')
        return gps_df
    
    @staticmethod
    def calc_front_travel( fork_mm, head_angle ):
        linear_travel = fork_mm * math.sin(head_angle)
        return round( linear_travel, 1 )
    
    @staticmethod
    def calc_travel_speed_mm_s( travel_diff_mm, time_diff_ms ):
        return (( travel_diff_mm * 1000 ) / time_diff_ms )
    
    @staticmethod
    def transform_travel_data( travel_df, setup: BmtSetup ):
        # Tranform ADC values to mm.
        fork_calculator = BmtCalculationsAdc2Mm( setup.fork_sensor() )
        shock_calculator = BmtCalculationsAdc2Mm( setup.shock_sensor() )

        travel_df['fork_mm'] = travel_df.apply( lambda row: fork_calculator.adc2mm(row.fork_adc), axis=1)
        travel_df['shock_mm'] = travel_df.apply( lambda row: shock_calculator.adc2mm(row.shock_adc), axis=1)

        # Calculate linear front end travel
        travel_df['front_end_lin_mm'] = travel_df.apply( lambda row: BmtCalculations.calc_front_travel( row.fork_mm, setup.bike().head_angle() ), axis=1)
        # TODO calculate bike rear end linear travel

        # Calculate tick differences
        travel_df['tick_diff'] = travel_df['int_timestamp'].diff()
        # Calculate front end speeds
        travel_df['front_diff_mm'] = travel_df['front_end_lin_mm'].diff().round(1)
        travel_df['front_speeds_mm_s'] = travel_df.apply( lambda row: BmtCalculations.calc_travel_speed_mm_s( row.front_diff_mm, row.tick_diff ), axis=1)
        # TODO Calculate read end speeds
        
        return travel_df

    




    
    

