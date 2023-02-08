#ifndef _GPS_COLL_H_
#define _GPS_COLL_H_

#include <stdint.h>

void gps_collector_init( void );
void gps_collector_deinit( void );
int gps_collector_grab_data( uint8_t * buffer, uint16_t max_length );

#endif