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
b           | Break Usage
s           | Speed (Wheel Speed)


## Data format

The single blocks of data are written to the file as they arrive from the measurement peripherals. As the first 4 bytes of every block contain the type and the length of a block a parser can read the data after it has been saved and downloaded.

### Travel Information

Fork and Read Shock data is stored as raw ADC data. Calibration information for every sensor is needed to correctly interpret the travel data.

Within a travel information block the first 16 bit are the fork travel data and the following 16-Bit are the shoch travel data. This means there will always be 32 bit blocks containing on set of travel information for fork and shock.

### GPS Data

GPS Data is NMEA0813 formated and will be saved as it is read from the module.


## Post Processing

Python scripts for post processing and data evaluation will be provided. The goal is to have a graphical interface for download and evaluation of data.






