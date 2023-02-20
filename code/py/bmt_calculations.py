import math
import pandas as pd
import json
from pyproj import Transformer
from bmt_formats import BmtSetup, BmtBike, BmtSensorCalibration

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
        return round(mm_val, 1 )

class BmtLevRatioCalculations:
    def __init__( self, json_path ):
        self._leverage_df = self._json_lev_to_travel_data( json_path )
    
    def _read_json( self, json_file ):
        try:
            with open( json_file ) as json_data:
                data = json.load( json_data )
        except:
            print( "Error reading: {}".format( json_file ) )
            return None
        
        return data

    def _json_lev_to_travel_data( self, json_path ):
        json_data = self._read_json( json_path )
        try:
            lev_df = pd.DataFrame(json_data['leverage_ratio_curve'])
        except KeyError:
            print( "No valid leverage ratio data file given.")
            return pd.DataFrame()
        
        lev_df['rear_wheel_diff_mm'] = lev_df['rear_wheel_mm'].diff().round(2)
        lev_df.loc[0, 'shock_diff_mm'] = 0
        for i in range(1, len(lev_df)):
            lev_df.loc[i, 'shock_diff_mm'] = (lev_df.loc[i, 'rear_wheel_diff_mm'] /lev_df.loc[i-1, 'leverage_ratio']).round(2)
        lev_df.loc[0, 'calc_shock_mm'] = 0
        for i in range(1, len(lev_df)):
            lev_df.loc[i, 'calc_shock_mm'] = lev_df.loc[i-1, 'calc_shock_mm'] + lev_df.loc[i, 'shock_diff_mm']
        # Calulate offset for quicker calcultions afterwards
        for i in range( 0, len(lev_df)):
            lev_df.loc[i, 'calc_offset'] = (lev_df.loc[i, 'rear_wheel_mm'] - ( lev_df.loc[i, 'leverage_ratio']*lev_df.loc[i, 'calc_shock_mm'])).round(2)

        return lev_df
    
    def shock_mm_to_rear_travel_mm( self, shock_mm : float ):
        for index in range( 0, len(self._leverage_df)):
            if self._leverage_df.loc[index, 'calc_shock_mm'] > shock_mm:
                break
        if ( index > 0 ):
            index -= 1
        rear_axle_mm = ( (shock_mm * self._leverage_df.loc[index, 'leverage_ratio']) + self._leverage_df.loc[index, 'calc_offset'] ).round(2)

        return rear_axle_mm
    
    def get_leverage_dataframe( self ):
        return self._leverage_df

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
        rear_axle_calculator = BmtLevRatioCalculations( setup.bike().frame_linkage())

        travel_df['fork_mm'] = travel_df.apply( lambda row: fork_calculator.adc2mm(row.fork_adc), axis=1)
        travel_df['shock_mm'] = travel_df.apply( lambda row: shock_calculator.adc2mm(row.shock_adc), axis=1)

        # Calculate linear front end travel
        travel_df['front_axle_mm'] = travel_df.apply( lambda row: BmtCalculations.calc_front_travel( row.fork_mm, setup.bike().head_angle() ), axis=1)
        travel_df['rear_axle_mm'] = travel_df.apply( lambda row: rear_axle_calculator.shock_mm_to_rear_travel_mm(row.shock_mm), axis=1 )

        # Calculate tick differences
        travel_df['tick_diff'] = travel_df['int_timestamp'].diff()
        # Calculate front end speeds
        travel_df['front_diff_mm'] = travel_df['front_axle_mm'].diff().round(1)
        travel_df['front_speeds_mm_s'] = travel_df.apply( lambda row: BmtCalculations.calc_travel_speed_mm_s( row.front_diff_mm, row.tick_diff ), axis=1)
        # TODO Calculate read end speeds
        travel_df['rear_diff_mm'] = travel_df['rear_axle_mm'].diff().round(1)
        travel_df['rear_speeds_mm_s'] = travel_df.apply( lambda row: BmtCalculations.calc_travel_speed_mm_s( row.rear_diff_mm, row.tick_diff ), axis=1)
        
        return travel_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BMT related calculations")
    parser.add_argument( "-j", "--json", dest="json_file", action="store", required=True, help="Path to json leverage ration file" )
    args = parser.parse_args()
    
    shock_calc = BmtLevRatioCalculations(args.json_file)
    print( shock_calc.get_leverage_dataframe())
    print( shock_calc.shock_mm_to_rear_travel_mm( 20 ) )

    
    

