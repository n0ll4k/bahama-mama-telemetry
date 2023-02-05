#ifndef _DATA_COLLECTOR_H
#define _DATA_COLLECTOR_H

#include "pico/util/queue.h"

int data_collector_init( queue_t * data_queue );
int data_collector_collect_and_push( void );

#endif