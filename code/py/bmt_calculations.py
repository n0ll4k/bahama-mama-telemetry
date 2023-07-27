import math
import pandas as pd
from pyproj import Transformer
from leverage import LevRatio
from bmt_formats import BmtSetup, BmtBike, BmtSensorCalibration
from scipy import signal

lonlat_to_webmercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

class BmtCalculationsAdc2Mm:
    def __init__( self, sensor_info: BmtSensorCalibration ):
        self._gradient = sensor_info.range_mm() / ( sensor_info.adc_value_max()-sensor_info.adc_value_zero())
        self._offset = sensor_info.range_mm() - ( (sensor_info.range_mm()*sensor_info.adc_value_max()) / ( sensor_info.adc_value_max()-sensor_info.adc_value_zero()) )
        self._sensor_info = sensor_info
    
    def adc2mm( self, adc_val ):
        mm_val = adc_val * self._gradient + self._offset
        if self._sensor_info.flip_travel() == True:
            mm_val = self._sensor_info.range_mm() - mm_val
        if( mm_val < 0 ):
            mm_val = 0.0
        return round(mm_val, 2 )

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
        linear_travel = fork_mm * math.sin(math.radians(head_angle))
        return round( linear_travel, 3 )
    
    @staticmethod
    def calc_travel_speed_mm_s( travel_diff_mm, time_diff_ms ):
        return (( travel_diff_mm * 1000 ) / time_diff_ms )
    
    @staticmethod
    def transform_travel_data( travel_df, setup: BmtSetup ):
        # Tranform ADC values to mm.
        fork_calculator = BmtCalculationsAdc2Mm( setup.fork_sensor() )
        shock_calculator = BmtCalculationsAdc2Mm( setup.shock_sensor() )
        rear_axle_calculator = LevRatio( setup.bike().frame_linkage())
        front_linear_max_mm = setup.bike().travel_fork_mm() * math.sin(math.radians(setup.bike().head_angle()))

        # Create filtered adc_values
        travel_df['fork_adc_filter'] = signal.savgol_filter(travel_df['fork_adc'] ,window_length=11,polyorder=3, mode="nearest")
        travel_df['shock_adc_filter'] = signal.savgol_filter(travel_df['shock_adc'] ,window_length=11,polyorder=3, mode="nearest")

        travel_df['fork_mm'] = travel_df.apply( lambda row: fork_calculator.adc2mm(row.fork_adc), axis=1)
        travel_df['shock_mm'] = travel_df.apply( lambda row: shock_calculator.adc2mm(row.shock_adc), axis=1)

        travel_df['fork_filter_mm'] = travel_df.apply( lambda row: fork_calculator.adc2mm(row.fork_adc_filter), axis=1)
        travel_df['shock_filter_mm'] = travel_df.apply( lambda row: shock_calculator.adc2mm(row.shock_adc_filter), axis=1)

        # Calculate linear front end travel
        travel_df['front_axle_mm'] = travel_df.apply( lambda row: BmtCalculations.calc_front_travel( row.fork_mm, setup.bike().head_angle() ), axis=1)
        travel_df['rear_axle_mm'] = travel_df.apply( lambda row: rear_axle_calculator.shock_mm_to_rear_travel_mm(row.shock_mm), axis=1 )

        travel_df['front_axle_filter_mm'] = travel_df.apply( lambda row: BmtCalculations.calc_front_travel( row.fork_filter_mm, setup.bike().head_angle() ), axis=1)
        travel_df['rear_axle_filter_mm'] = travel_df.apply( lambda row: rear_axle_calculator.shock_mm_to_rear_travel_mm(row.shock_filter_mm), axis=1 )

        # Calculate tick differences
        travel_df['tick_diff'] = travel_df['int_timestamp'].diff()
        
        # Calculate travel percentages
        travel_df['front_percentage'] = travel_df.apply( lambda row: ((row.front_axle_filter_mm/front_linear_max_mm)*100).round(1), axis=1)
        travel_df['rear_percentage'] = travel_df.apply( lambda row: ((row.rear_axle_filter_mm/setup.bike().travel_rear_axle_mm())*100).round(1) ,axis=1)
        
        return travel_df
    
    def calculate_travel_speeds( travel_df ):
        # Calculate front end speeds
        travel_df['front_diff_mm'] = travel_df['front_axle_filter_mm'].diff().round(4)
        travel_df['front_speeds_mm_s'] = travel_df.apply( lambda row: BmtCalculations.calc_travel_speed_mm_s( row.front_diff_mm, row.tick_diff ), axis=1)
        # Calculate read end speeds
        travel_df['rear_diff_mm'] = travel_df['rear_axle_filter_mm'].diff().round(4)
        travel_df['rear_speeds_mm_s'] = travel_df.apply( lambda row: BmtCalculations.calc_travel_speed_mm_s( row.rear_diff_mm, row.tick_diff ), axis=1)

        return travel_df



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BMT related calculations")
    parser.add_argument( "-j", "--json", dest="json_file", action="store", required=True, help="Path to json leverage ration file" )
    args = parser.parse_args()
    
    shock_calc = LevRatio(args.json_file)
    print( shock_calc.get_leverage_dataframe())
    print( shock_calc.shock_mm_to_rear_travel_mm( 20 ) )
