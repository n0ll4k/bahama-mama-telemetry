import struct
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
        start_idx = 0
        end_idx = 4        
        data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[start_idx:end_idx])
        start_idx = end_idx
        end_idx += data_header[2]
        

        print( data_header )
        BmtLogReader.parse_travel_information( raw_data[start_idx:end_idx] )
        
        """
        data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[2008:2012])
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP, raw_data[2012:2016])

        print( data_header )
        print( timestamp)
        """

    @staticmethod
    def parse_travel_information( travel_raw_data ):
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP, travel_raw_data[0:4])
        print( timestamp )
        travel_information = struct.unpack( bmt_fmt.TRAVEL_INFORMATION, travel_raw_data[4:8])
        print( travel_information )
    


        



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reads BMT files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()


    BmtLogReader.parse_file( args.file )