#include <string.h>
#include "pico/stdlib.h"

#include "data_collector.h"
#include "../adc_collector/adc_collector.h"
#include "../gps_collector/gps_collector.h"
//---------------------------------------------------------------------------
#define HEADER_OFF      1
#define TIMESTAMP_OFF   1
/* Data offset within travel data for MAX_BUFFER_SIZE. Header & timestamp.*/
#define TRAVEL_DATA_OFF (HEADER_OFF+TIMESTAMP_OFF)
/* As two samples are stored in 1 uint32_t we need only half the buffer. */
#define BUFFERSIZE      ((NUM_SAMPLES/2)+TRAVEL_DATA_OFF)
#define TRAVEL_ID       't'
#define GPS_ID          'g'
#define ACC_ID          'a'
#define BRAKE_ID        'b'
#define SPEED_ID        's'
#define GPS_SAMPLES     256
//---------------------------------------------------------------------------
#pragma pack(2)
typedef struct data_header_s {
    uint8_t data_type;
    uint8_t reserved;
    uint16_t block_length;
} data_header_t;

typedef struct travel_info_s {
    uint16_t fork_data;
    uint16_t shock_data;
} travel_info_t;

#pragma pack(0)

uint16_t * adc_data = NULL;
uint16_t adc_buffer[NUM_SAMPLES];
queue_t * data_queue = NULL;
uint32_t data_buffer[BUFFERSIZE];
uint8_t gps_buf[GPS_SAMPLES];
//---------------------------------------------------------------------------

int data_collector_init( queue_t * queue )
{
    data_queue = queue;

    /* Initialize the ADC hardware */
    adc_data = adc_collector_init();
    if ( NULL == adc_data ) {
        return -1;
    }
    
    return 0;
}

void data_collector_start( void )
{   
    gps_collector_init();
    adc_collector_start_adc();
}

void data_collector_stop( void )
{
    gps_collector_deinit();
    adc_collector_stop_adc();
}

int data_collector_collect_and_push( void )
{   
    int idx = 0;
    int adc_idx = 0;
    int gps_bytes = 0;
    int gps_remainder = 0;
    uint32_t temp_var = 0;
    uint32_t timestamp = 0;
    travel_info_t travel_info;
    data_header_t header = { 
        .data_type = 0x00,
        .reserved = 0x00,
        .block_length = 0
    };

    /* Wait for ADC data. */
    adc_data = adc_collector_wait_for_new_data( &timestamp );
    memcpy( adc_buffer, adc_data, sizeof(uint16_t)*NUM_SAMPLES );
    
    /* Build ADC data stream. */
    idx = 0;
    header.data_type = TRAVEL_ID;
    header.block_length = NUM_SAMPLES*2 + 4;    /* Length is given in 8-bit. 16-Bit samples + 32-Bit timestamp*/
    if ( data_queue != NULL ) {
        queue_add_blocking( data_queue, (uint32_t*)&header);    /* Add Header to stream. */
        queue_add_blocking( data_queue, &timestamp);            /* Add timestamp to stream. */
        for ( adc_idx = 0; idx < BUFFERSIZE, adc_idx < NUM_SAMPLES; idx++, adc_idx+=2 ) {
            temp_var  = ((adc_buffer[adc_idx+1] << 16) & 0xFFFF0000);
            temp_var |= (adc_buffer[adc_idx] & 0x0000FFFF);
            queue_add_blocking(data_queue, &temp_var );
        }
    }

    /* Check if new GPS data is available. */    
    gps_bytes = gps_collector_grab_data( gps_buf, GPS_SAMPLES );
    if ( gps_bytes > 0 ) {
        header.data_type =  GPS_ID;
        
        /* Length is given in 8-bit. GPS length always has to be a multiple of 4. */
        gps_remainder = gps_bytes % 4;
        if ( gps_remainder != 0 ) {
            header.block_length = ( gps_bytes - gps_remainder ) + 4;
        } else {
            header.block_length = ( gps_bytes - gps_remainder );
        }
    
        if ( data_queue != NULL ) {
            queue_add_blocking(data_queue, (uint32_t*)&header);
            if ( gps_bytes > 0 ) {
                for ( idx = 0; idx < (gps_bytes-gps_remainder); idx+=4 ) {
                    temp_var  = ((gps_buf[idx+3] << 24) & 0xFF000000);
                    temp_var |= ((gps_buf[idx+2] << 16) & 0x00FF0000);
                    temp_var |= ((gps_buf[idx+1] << 8) & 0x0000FF00);
                    temp_var |= ((gps_buf[idx]) & 0x000000FF);
                    queue_add_blocking(data_queue, &temp_var);
                }
            }
            switch( gps_remainder ) {
                case 3:
                    temp_var  = ((0x00 << 24) & 0xFF000000);
                    temp_var |= ((gps_buf[idx+2] << 16) & 0x00FF0000);
                    temp_var |= ((gps_buf[idx+1] << 8) & 0x0000FF00);
                    temp_var |= ((gps_buf[idx]) & 0x000000FF);
                    queue_add_blocking(data_queue, &temp_var);
                    break;
                case 2:
                    temp_var  = ((0x00 << 24) & 0xFF000000);
                    temp_var |= ((0x00 << 16) & 0x00FF0000);
                    temp_var |= ((gps_buf[idx+1] << 8) & 0x0000FF00);
                    temp_var |= ((gps_buf[idx]) & 0x000000FF);
                    queue_add_blocking(data_queue, &temp_var);
                    break;
                case 1:
                    temp_var  = ((0x00 << 24) & 0xFF000000);
                    temp_var |= ((0x00 << 16) & 0x00FF0000);
                    temp_var |= ((0x00 << 8) & 0x0000FF00);
                    temp_var |= ((gps_buf[idx]) & 0x000000FF);
                    queue_add_blocking(data_queue, &temp_var);
                    break;
                case 0:
                default:
                    break;
            }
        }
    }
    return 0;
}
