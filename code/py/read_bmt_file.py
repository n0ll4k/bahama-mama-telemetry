import struct
import os
import pynmea2
import datetime
import bmt_formats as bmt_fmt
import pandas as pd


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
    def parse_file( file_path ):
        gps_str = ""
        print( "Reading data file: {}".format( file_path) )
        raw_data = BmtLogReader._read_file( file_path )
             
        
        while( len(raw_data) > 0 ):
            data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[:struct.calcsize(bmt_fmt.DATA_HEADER_FMT)])
            raw_data = raw_data[struct.calcsize(bmt_fmt.DATA_HEADER_FMT):]
            if ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b't' ):
                print( data_header)
                BmtLogReader.parse_travel_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]] )
            elif ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b'g'):
                gps_str = BmtLogReader.collect_gps_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]], gps_str)
            else:
                print( "Unknown Block: {} | Length: {}".format(data_header[bmt_fmt.DATA_HEADER_POS_TYPE], data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]))
            
            raw_data = raw_data[data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]:]

        gps_data = BmtLogReader.parse_gps_information( gps_str)
        gps_filename = "{}-{}_{}.csv".format(os.path.basename(file_path[:-4]), datetime.date.strftime(gps_data[0]['date'], "%Y-%m-%d"), datetime.time.strftime(gps_data[0]['timestamp'], "%H-%M-%S") )
        gps_path = os.path.join( os.path.abspath(os.path.dirname(file_path)), gps_filename )
        gps_df = pd.DataFrame.from_dict( gps_data )
        
        gps_df.to_csv(gps_path)



    @staticmethod
    def parse_travel_information( travel_raw_data  ):
        #TODO: Save data sets (To DB?)
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP_FMT, travel_raw_data[0:struct.calcsize(bmt_fmt.TIMESTAMP_FMT)])
        print( timestamp )
        travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TIMESTAMP_FMT):]
        
        while( len(travel_raw_data) >= struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT) ):
            travel_information = struct.unpack( bmt_fmt.TRAVEL_INFORMATION_FMT, travel_raw_data[:struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT)])
            travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT):]
            #print( travel_information )

    @staticmethod
    def collect_gps_information( gps_stream_data, gps_raw_storage ):
        new_gps_data = gps_stream_data.decode().rstrip( '\x00')
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
                msg = pynmea2.parse(sentence)
                if type(msg) == pynmea2.types.talker.VTG:
                    gps_dict['speed'] = msg.spd_over_grnd_kmph
                elif type(msg) == pynmea2.types.talker.GGA:
                    gps_dict['timestamp'] = msg.timestamp
                    gps_dict['lat'] = msg.lat
                    gps_dict['lat_dir'] = msg.lat_dir
                    gps_dict['lon'] = msg.lon
                    gps_dict['lon_dir'] = msg.lon_dir
                    gps_dict['altitude'] = msg.altitude
                    gps_dict['altitude_unit'] = msg.altitude_units
                elif type(msg) == pynmea2.types.talker.RMC:
                    gps_dict['date'] = msg.datestamp
                else:
                    print( "Error UNKNON sentence appeared.")
            gps_dict_list.append( gps_dict )
        
        return gps_dict_list
            
        
        
    


        



if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description="Reads BMT files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()
    
    BmtLogReader.parse_file( args.file )