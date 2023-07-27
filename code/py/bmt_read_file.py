import struct
import os
import pynmea2
import datetime
import json
import bmt_formats as bmt_fmt
import pandas as pd
from bmt_calculations import BmtCalculations



class BmtLogReader:
    @staticmethod
    def _read_file( file_path ):
        try:
            with open(file_path, "rb") as file:
                raw_data = file.read()
        except:
            print( "Error reading data file: {}".format(file_path) )
        else:
            return raw_data

    @staticmethod
    def process_data(file_path, setup: bmt_fmt.BmtSetup):
        travel_df, gps_df = BmtLogReader.parse_file(file_path)

        BmtCalculations.transform_gps_data( gps_df )
        BmtCalculations.transform_travel_data( travel_df, setup )
        BmtCalculations.calculate_travel_speeds( travel_df )
        
        try:
            base_filename = "{}-{}_{}_".format(os.path.basename(file_path[:-4]), 
                                            datetime.date.strftime(gps_df.loc[0]['date'], "%Y-%m-%d"), 
                                            datetime.time.strftime(gps_df.loc[0]['timestamp'], "%H-%M-%S") )
        except:
            base_filename = "{}_".format(os.path.basename(file_path[:-4]))
        gps_filename = "{}GPS.csv".format(base_filename)
        travel_filename = "{}TRAVEL.csv".format(base_filename)
        gps_path = os.path.join( os.path.abspath(os.path.dirname(file_path)), gps_filename )
        travel_path = os.path.join( os.path.abspath(os.path.dirname(file_path)), travel_filename )

        
        gps_df.to_csv(gps_path)
        travel_df.to_csv(travel_path)
        return (travel_path, gps_path)



    @staticmethod
    def read_sensor_calib( json_path ):
        try:
            with open( json_path ) as file:
                json_data = json.load(file)
        except:
            print( "Error reading sensor calibration data.")
            return BmtSensorCalibration()
        
        sensor = BmtSensorCalibration()
        sensor.set_sensor_name( json_data['sensor_name'])
        sensor.set_adc_value_zero( json_data['adc_val_zero'])
        sensor.set_adc_value_max( json_data['adc_val_max'])
        sensor.set_range_mm( json_data['range_mm'])
        sensor.flip_travel( json_data['flip_travel'])

        return sensor
    
    @staticmethod
    def parse_file( file_path ):
        gps_str = ""
        travel_info_list = list()
        print( "Reading data file: {}".format( file_path) )
        raw_data = BmtLogReader._read_file( file_path )
                
        while( len(raw_data) > 0 ):
            data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[:struct.calcsize(bmt_fmt.DATA_HEADER_FMT)])
            raw_data = raw_data[struct.calcsize(bmt_fmt.DATA_HEADER_FMT):]
            if ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b't' ):
                # Collect all travel data
                travel_info_list.extend(BmtLogReader.parse_travel_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]] ))
            elif ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b'g'):
                # Collect complete GPS stream
                gps_str = BmtLogReader.collect_gps_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]], gps_str)
            else:
                print( "Unknown Block: {} | Length: {}".format(data_header[bmt_fmt.DATA_HEADER_POS_TYPE], data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]))
            
            raw_data = raw_data[data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]:]
        # Correct timestamp
        start_timestamp = travel_info_list[0]['int_timestamp']
        for dataset in travel_info_list:
            dataset['int_timestamp'] = dataset['int_timestamp'] - start_timestamp
        # Parse all GPS data
        gps_data = BmtLogReader.parse_gps_information( gps_str)
        
        # Add data to dataframes for easy storage
        travel_df = pd.DataFrame.from_dict( travel_info_list )
        gps_df = pd.DataFrame.from_dict( gps_data )

        return ( travel_df, gps_df )


    @staticmethod
    def parse_travel_information( travel_raw_data  ):
        travel_information_list = list()
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP_FMT, travel_raw_data[0:struct.calcsize(bmt_fmt.TIMESTAMP_FMT)])[0]
        travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TIMESTAMP_FMT):]
        
        while( len(travel_raw_data) >= struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT) ):
            travel_info_dict = dict()
            travel_information = struct.unpack( bmt_fmt.TRAVEL_INFORMATION_FMT, travel_raw_data[:struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT)])
            travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT):]
            travel_info_dict['int_timestamp'] = timestamp
            travel_info_dict['fork_adc'] = travel_information[0]
            travel_info_dict['shock_adc'] = travel_information[1]
            timestamp += 1
            travel_information_list.append(travel_info_dict)

        return travel_information_list

    @staticmethod
    def collect_gps_information( gps_stream_data, gps_raw_storage ):
        try:
            new_gps_data = gps_stream_data.decode().rstrip( '\x00')
        except UnicodeDecodeError:
            print( "Error decoding ")
            new_gps_data = ""
        gps_raw_storage += new_gps_data
        return gps_raw_storage

    @staticmethod
    def parse_gps_information( gps_raw_data ):
        relevant_sentences = list()
        gps_dict_list = list()

        # Grab relevant sentences.
        gps_raw_lines = gps_raw_data.splitlines()
        for sentence in gps_raw_lines:
            for header in bmt_fmt.GPS_SENTENCES:
                if sentence.startswith(header):
                    relevant_sentences.append(sentence)
                    break

        # Get relevant chunks from data        
        chunks = [relevant_sentences[x:x+len(bmt_fmt.GPS_SENTENCES)] for x in range(0, len(relevant_sentences), len(bmt_fmt.GPS_SENTENCES))]
        
        # Grab data from chunks
        for sentences in chunks:
            gps_dict = dict()
            for sentence in sentences:
                try:
                    msg = pynmea2.parse(sentence)
                except:
                    continue
                if type(msg) == pynmea2.types.talker.VTG:
                    try:
                        gps_dict['speed'] = float(msg.spd_over_grnd_kmph)
                    except:
                        gps_dict['speed'] = 0.0
                elif type(msg) == pynmea2.types.talker.GGA:
                    try:
                        gps_dict['timestamp'] = msg.timestamp
                        gps_dict['lat'] = float(msg.lat)
                        gps_dict['lat_dir'] = msg.lat_dir
                        gps_dict['lon'] = float(msg.lon)
                        gps_dict['lon_dir'] = msg.lon_dir
                        gps_dict['altitude'] = float(msg.altitude)
                        gps_dict['altitude_unit'] = msg.altitude_units
                    except:
                        gps_dict['timestamp'] = 0
                        gps_dict['lat'] = 0.0
                        gps_dict['lat_dir'] = 'N'
                        gps_dict['lon'] = 0.0
                        gps_dict['lon_dir'] = 'E'
                        gps_dict['altitude'] = 0.0
                        gps_dict['altitude_unit'] = 'm'
                        print( "Error parsing GGA.")
                elif type(msg) == pynmea2.types.talker.RMC:
                    gps_dict['date'] = msg.datestamp
                else:
                    print( "Error UNKNON sentence appeared.")
            gps_dict_list.append( gps_dict )
        
        return gps_dict_list
            
if __name__ == "__main__":
    import argparse
    from bmt_calculations import BmtCalculations
    from bmt_formats import BmtSensorCalibration, BmtBike, BmtSetup
    parser = argparse.ArgumentParser(description="Reads BMT files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()

    fork_sensor_dummy = BmtSensorCalibration()
    fork_sensor_dummy.set_adc_value_zero( 25 ) 
    fork_sensor_dummy.set_adc_value_max( 4095 )
    fork_sensor_dummy.set_range_mm( 200 )
    fork_sensor_dummy.set_flip_travel(True)

    shock_sensor_dummy = BmtSensorCalibration()
    shock_sensor_dummy.set_adc_value_zero( 22 ) 
    shock_sensor_dummy.set_adc_value_max( 4095 )
    shock_sensor_dummy.set_range_mm( 75 )
    shock_sensor_dummy.set_flip_travel(False)

    dummy_bike = BmtBike()
    dummy_bike.set_bike_name( "Kavenz VHP16 Fred")
    dummy_bike.set_head_angle( 64.0 )
    dummy_bike.set_travel_rear_mm(160)
    dummy_bike.set_travel_fork_mm(170)
    dummy_bike.set_travel_shock_mm(65)
    dummy_bike.set_frame_linkage("/Users/n0ll4k/Documents/bmt_data/travel_data/Kavenz_VHP16.json")

    das_setup = BmtSetup()
    das_setup.set_fork_sensor( fork_sensor_dummy )
    das_setup.set_shock_sensor( shock_sensor_dummy )
    das_setup.set_bike( dummy_bike )

    BmtLogReader.process_data(args.file, das_setup)
    