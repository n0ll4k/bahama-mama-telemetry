/**
 * Simple C FIFO to buffer incoming GPS data.
 */

#include "gps_fifo.h"

uint8_t buffer[FIFO_SIZE];
uint16_t head = 0;
uint16_t tail = 0;

void gps_fifo_push( uint8_t data )
{
    buffer[head] = data;

    head++;

    if ( head >= FIFO_SIZE ) {
        head = 0;
    }
}

void gps_fifo_pop( uint8_t * data )
{
    *data = buffer[tail];

    tail++;
    if ( tail >= FIFO_SIZE ) {
        tail = 0;
    }

}

uint16_t gps_fifo_level( void )
{
    uint16_t level = 0;

    if ( head >= tail ) {
        level = head - tail;
    } else {
        level = FIFO_SIZE + head - tail;
    }

    return level;
}