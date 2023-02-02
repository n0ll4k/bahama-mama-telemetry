#ifndef _ADC_COLL_H
#define _ADC_COLL_H

#include <stdlib.h>
#include <stdbool.h>

#define NUM_SAMPLES     1000

typedef struct adc_coll_data_s {
    int sample_channel;
    int ctrl_channel;
    uint16_t * p_data;
} adc_coll_data_t;

adc_coll_data_t * adc_coll_init( void );
void adc_coll_start_adc( void );
void adc_coll_wait_for_new_data( adc_coll_data_t * adc_data );

#endif