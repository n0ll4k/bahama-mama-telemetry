import struct
import os
import bmt_formats as bmt_fmt

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
        print( "Reading data file: {}".format( file_path) )
        raw_data = BmtLogReader._read_file( file_path )
             
        
        while( len(raw_data) > 0 ):
            data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[:struct.calcsize(bmt_fmt.DATA_HEADER_FMT)])
            raw_data = raw_data[struct.calcsize(bmt_fmt.DATA_HEADER_FMT):]
            if ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b't' ):
                print( data_header)
                BmtLogReader.parse_travel_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]] )
            elif ( data_header[bmt_fmt.DATA_HEADER_POS_TYPE] == b'g'):
                BmtLogReader.parse_gps_information( raw_data[:data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]])
            else:
                print( "Unknown Block: {} | Length: {}".format(data_header[bmt_fmt.DATA_HEADER_POS_TYPE], data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]))
            
            raw_data = raw_data[data_header[bmt_fmt.DATA_HEADER_POS_LENGTH]:]



    @staticmethod
    def parse_travel_information( travel_raw_data  ):
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP_FMT, travel_raw_data[0:struct.calcsize(bmt_fmt.TIMESTAMP_FMT)])
        print( timestamp )
        travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TIMESTAMP_FMT):]
        
        while( len(travel_raw_data) >= struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT) ):
            travel_information = struct.unpack( bmt_fmt.TRAVEL_INFORMATION_FMT, travel_raw_data[:struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT)])
            travel_raw_data = travel_raw_data[struct.calcsize(bmt_fmt.TRAVEL_INFORMATION_FMT):]
            #print( travel_information )

    @staticmethod
    def parse_gps_information( gps_raw_data ):
        print( gps_raw_data )
    


        



if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description="Reads BMT files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()
    
    BmtLogReader.parse_file( args.file )