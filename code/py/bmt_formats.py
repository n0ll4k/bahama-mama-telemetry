DATA_HEADER_POS_TYPE = 0
DATA_HEADER_POS_RES = 1
DATA_HEADER_POS_LENGTH = 2

DATA_HEADER_FMT = '<cBH'
# [0]: uint8    - Data type
# [1]: uint8    - Reserved
# [2]: uint16   - Data length

TIMESTAMP_FMT = '<L'
# [0]: uint32   - timestamp

TRAVEL_INFORMATION_FMT = '<HH'
# [0]: uint16   - Fork ADC data
# [1]: uint16   - Shock ADC data