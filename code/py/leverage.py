# JSON
import json
# Pandas (mainly DataFrame)
import pandas as pd

class LevRatio:
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
        
        lev_df['rear_wheel_diff_mm'] = lev_df['rear_wheel_mm'].diff().round(4)
        lev_df.loc[0, 'shock_diff_mm'] = 0
        for i in range(1, len(lev_df)):
            lev_df.loc[i, 'shock_diff_mm'] = (lev_df.loc[i, 'rear_wheel_diff_mm'] /lev_df.loc[i-1, 'leverage_ratio']).round(4)
        lev_df.loc[0, 'calc_shock_mm'] = 0
        for i in range(1, len(lev_df)):
            lev_df.loc[i, 'calc_shock_mm'] = lev_df.loc[i-1, 'calc_shock_mm'] + lev_df.loc[i, 'shock_diff_mm']
        # Calulate offset for quicker calculations afterwards
        for i in range( 0, len(lev_df)):
            lev_df.loc[i, 'calc_offset'] = (lev_df.loc[i, 'rear_wheel_mm'] - ( lev_df.loc[i, 'leverage_ratio']*lev_df.loc[i, 'calc_shock_mm'])).round(4)

        return lev_df
    
    def shock_mm_to_rear_travel_mm( self, shock_mm : float ):
        for index in range( 0, len(self._leverage_df)):
            if self._leverage_df.loc[index, 'calc_shock_mm'] > shock_mm:
                break
        if ( index > 0 ):
            index -= 1
        rear_axle_mm = ( (shock_mm * self._leverage_df.loc[index, 'leverage_ratio']) + self._leverage_df.loc[index, 'calc_offset'] ).round(4)

        return rear_axle_mm
    
    def get_leverage_dataframe( self ):
        return self._leverage_df