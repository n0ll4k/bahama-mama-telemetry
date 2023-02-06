import struct
import binascii
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
        print( raw_data[:4] )
        
        
        data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[:4])
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP, raw_data[4:8])

        print( data_header )
        print( timestamp)
        """
        data_header = struct.unpack( bmt_fmt.DATA_HEADER_FMT, raw_data[2008:2012])
        timestamp = struct.unpack( bmt_fmt.TIMESTAMP, raw_data[2012:2016])

        print( data_header )
        print( timestamp)
        """
        
        



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reads BMT files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()


    BmtLogReader.parse_file( args.file )