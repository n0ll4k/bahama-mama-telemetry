# File Format


There will be one file for each data recording started. The files will be named after the internal time tick they were started at. A normalized datetime format will be available through the GPS data inside the file. Files won't be human readable as hex/ascii data will be saved to gain a bit of speed.

Current plan is to write blocks of data in case the buffers are at the edge of an overflow or in specific time slots.

## Header Information

The blocks will have a header with the following content:

Byte Position | Content
--------------|---------
0 | Type of data 
1 | Reserved
2 | Reserved
3 | Reserved
4 | Internal time tick
8 | Bytes of data in block
12 | CRC32

CRC32 is currently open to discussion as it is depatable if it is needed and if enough processor time is available for creation / processing.


### Data Types

At the current point there are 2 different types of data. They are defined as followed:

Code | Type
-----|-----
0x01 | Fork mm data
0x02 | Rear Shock mm data
0x03 | GPS data

## Data format

Fork and Read Shock mm data will be saved as 16-bit unsigned integers. Steps will be 0.1mm which means a value of 100 will represent 10.0mm.

GPS data data will depend on the GPS module choosen. As currently no HW was choosen it is still open. Most likely it will be just the data stream from the serial data stream saved directly.


## Post Processing

Python scripts for post processing and data evaluation will be provided. The goal is to have a graphical interface for download and evaluation of data. This will most likely take a while :)






