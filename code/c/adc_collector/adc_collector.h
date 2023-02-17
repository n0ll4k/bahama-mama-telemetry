#ifndef _ADC_COLL_H
#define _ADC_COLL_H

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#define NUM_SAMPLES     1000

uint16_t * adc_collector_init( void );
void adc_collector_start_adc( void );
void adc_collector_stop_adc( void );
uint16_t * adc_collector_wait_for_new_data(  uint32_t * start_time );



#endif