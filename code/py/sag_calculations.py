# JSON
import json
# Math sinus
import math
# Leverage ratio class
from leverage import LevRatio

class SagCalculator:
    def __init__(self, json_path):
        self._bike_dict = self._read_bike_json(json_path)
        if self._bike_dict is not None:
            self._rear_travel_info = LevRatio(self._bike_dict['frame_linkage_file'])
        else:
            self._rear_travel_info = None
        

    def _read_bike_json(self, path_to_json):
        try:
            with open( path_to_json ) as json_data:
                data = json.load( json_data )
        except:
            print( "Error reading: {}".format( path_to_json ) )
            return None
        
        return data
    
    def calc_mm_from_sag( self, sag_in_pc: float ) -> tuple:
        rear_sag_mm = self._bike_dict['travel_rear_axle_mm'] * (sag_in_pc/100.0)
        fork_sag_mm = rear_sag_mm / math.sin(math.radians(self._bike_dict['head_angle']))
        shock_sag_mm = self._rear_travel_info.rear_travel_mm_to_shock_mm(rear_sag_mm)

        return ( round(fork_sag_mm, 2), round( shock_sag_mm, 2) )
        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SAG Calculations")
    parser.add_argument( "-j", "--json", dest="json_file", action="store", required=True, help="Path to json leverage ration file" )
    parser.add_argument( "-p", "--percent", dest="sag_in_pc", type=float, action="store", required=True, help="SAG in PC")
    args = parser.parse_args()

    sag_calc = SagCalculator(args.json_file)
    sag_data = sag_calc.calc_mm_from_sag( args.sag_in_pc )

    print( f"Fork SAG: {sag_data[0]}mm")
    print( f"Shock SAG: {sag_data[1]}mm")