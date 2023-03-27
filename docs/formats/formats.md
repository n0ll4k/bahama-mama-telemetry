# File Format

There will be one file for each data recording started. The files will be named after the internal time tick they were started at plus an index. A normalized datetime format will be available through the GPS data inside the file. Files won't be human readable as hex/ascii data will be saved to gain a bit of speed.

As the data shall be written to the file as they are measured. An identifier for every small block shall be used.

## Block Identifier

The block identifier shall fit into 32-Bit as uint32_t will be the dataype for the inter core queue.

Byte Position | Content
--------------|-----------------------------
0             | Data Type Identifier
1             | Reserved
2             | MSB Block Length (In Bytes)
3             | LSB Block Length (In Bytes)


### Data Type identifier

Identifier  | Data Content
------------|-----------------------------------------
t           | travel information (Fork & Shock)
g           | GPS Data
a           | Acceleration (Gyroscope & Accelerometer)
b           | Brake Usage
s           | Speed (Wheel Speed)


## Data format

The single blocks of data are written to the file as they arrive from the measurement peripherals. As the first 4 bytes of every block contain the type and the length of a block a parser can read the data after it has been saved and downloaded.

### Travel Information

Fork and Read Shock data is stored as raw ADC data. Calibration information for every sensor is needed to correctly interpret the travel data.

At the start of the block an internal timestamp will be stored. After that the fork and shock data is stored.

Within a travel information block the first 16 bit are the fork travel data and the following 16-Bit are the shoch travel data. This means there will always be 32 bit blocks containing on set of travel information for fork and shock.

### GPS Data

GPS Data is NMEA0813 formated and will be saved as it is read from the module.


## Post Processing

Python scripts for post processing and data evaluation will be provided. The goal is to have a graphical interface for download and evaluation of data.


# WiFi/TCP Protocol

Again the protocol will be designed having KISS in mind.

The BMT system will be the TCP server as it contains the data. A PC (Or in the future a smartphone) will be the client to the server.

To start with there will be two available commands from the client as shown in the table below, the commans will have a 16-Bit code:

Byte Code   | Command Name 
------------|-------------------------
0x0000      | Reserved (NOP)
0x0001      | Get last file
0x0002      | Get older file

As the main use case will be to retrieve the latest file from the system that will be the basic command. In addition a get older files command shall be implemented which everytime counts down and checks for an older file. If there is no older file an error/defined message will be returned.

The filestream shall include the filename, length and actual data. The byte offsets are as shown in the following table:

Byte Offset | Content
------------|------------------------------------
0           | Filename (Length always 13-Byte)
13          | Data length in Byte (32-Bit value)
17          | Start of actual data block