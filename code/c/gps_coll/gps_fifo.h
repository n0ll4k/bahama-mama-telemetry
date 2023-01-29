/**
 * Simple C FIFO to buffer incoming GPS data.
 */
#ifndef _GPS_FIFO_H_
#define _GPS_FIFO_H_

#include <stdint.h>

#define FIFO_SIZE   1024

void gps_fifo_push( uint8_t data );
void gps_fifo_pop( uint8_t * data );
uint16_t gps_fifo_level( void );

#endif
