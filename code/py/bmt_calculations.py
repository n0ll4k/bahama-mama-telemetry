import pandas as pd
from pyproj import Transformer

lonlat_to_webmercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

class BmtCalculationsAdc2Mm:
    def __init__( self, sensor_info: dict ):
        self._gradient = sensor_info['range_mm'] / ( sensor_info['adc_val_max']-sensor_info['adc_val_zero'])
        self._offset = sensor_info['range_mm'] - ( (sensor_info['range_mm']*sensor_info['adc_val_max']) / ( sensor_info['adc_val_max']-sensor_info['adc_val_zero']) )
    
    def adc2mm( self, adc_val ):
        mm_val = adc_val * self._gradient + self._offset
        return round(mm_val, 1 )

class BmtCalculations:
    @staticmethod
    def rad2dec( input, direction):
        deg = float(int( input / 100 )) 
        decimal =  deg + (( input - (deg * 100 )) / 60 )
        if direction in ['W', 'S']:
            decimal *= -1

        return( decimal )
    
    @staticmethod
    def lat_lon2x_y(lat, lon):
        x, y = lonlat_to_webmercator.transform(lon, lat)
        return [x, y]

    @staticmethod
    def adc_to_mm( input_df : pd.DataFrame, fork_calib: dict, shock_calib: dict ):
        fork_calc = BmtCalculationsAdc2Mm( fork_calib )
        shock_calc = BmtCalculationsAdc2Mm( shock_calib )

        input_df['fork_mm'] = input_df.apply( lambda row: fork_calc.adc2mm(row.fork_adc), axis=1)
        input_df['shock_mm'] = input_df.apply( lambda row: shock_calc.adc2mm(row.shock_adc), axis=1)
        
        return input_df
    
    @staticmethod
    def transform_gps_data( gps_df: pd.DataFrame ):
        gps_df['lat_dec'] = gps_df.apply( lambda row: BmtCalculations.rad2dec( row.lat, row.lat_dir ), axis=1)
        gps_df['lon_dec'] = gps_df.apply( lambda row: BmtCalculations.rad2dec( row.lon, row.lon_dir ), axis=1)
        gps_df[['x', 'y']] = gps_df.apply( lambda row: BmtCalculations.lat_lon2x_y( row.lat_dec, row.lon_dec ), axis=1, result_type='expand')
        return gps_df
    
    @staticmethod
    def transform_input_data( travel_df, gps_df ):

        return travel_df, gps_df

    




    
    

