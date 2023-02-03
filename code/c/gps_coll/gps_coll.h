#ifndef _GPS_COLL_H_
#define _GPS_COLL_H_

#include <stdint.h>

void gps_coll_init( void );
int gps_coll_grab_data( uint8_t * buffer, uint16_t max_length );

#endif