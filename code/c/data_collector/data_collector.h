#ifndef _DATA_COLLECTOR_H
#define _DATA_COLLECTOR_H

#include "pico/util/queue.h"

typedef struct queue_element {
    uint32_t value;
} queue_element_t;


int data_collector_init( queue_t * queue );
void data_collector_start( void );
void data_collector_stop( void );
int data_collector_collect_and_push( void );

#endif