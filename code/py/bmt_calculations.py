import pandas as pd

class BmtCalculationsAdc2Mm:
    def __init__( self, sensor_info: dict ):
        self._gradient = sensor_info['range_mm'] / ( sensor_info['adc_val_max']-sensor_info['adc_val_zero'])
        self._offset = sensor_info['range_mm'] - ( (sensor_info['range_mm']*sensor_info['adc_val_max']) / ( sensor_info['adc_val_max']-sensor_info['adc_val_zero']) )
    
    def adc2mm( self, adc_val ):
        mm_val = adc_val * self._gradient + self._offset
        return round(mm_val, 1 )



class BmtCalculations:
    @staticmethod
    def adc_to_mm( input_df : pd.DataFrame, fork_calib: dict, shock_calib: dict ):
        fork_calc = BmtCalculationsAdc2Mm( fork_calib )
        shock_calc = BmtCalculationsAdc2Mm( shock_calib )

        input_df['fork_mm'] = input_df.apply( lambda row: fork_calc.adc2mm(row.fork_adc), axis=1)
        input_df['shock_mm'] = input_df.apply( lambda row: shock_calc.adc2mm(row.shock_adc), axis=1)
        print( input_df )
        return input_df
        

