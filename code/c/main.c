/**
 * Bahama Mama Telemetry
 * by Frederik Krämer
 * 
 * 2023
 */
#include <stdint.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/gpio.h"

#include "f_util.h"
#include "ff.h"
#include "rtc.h"
#include "hw_config.h"

#include "adc_collector/adc_collector.h"
#include "gps_collector/gps_collector.h"
#include "gps_collector/gps_fifo.h"

#define GPS_SAMPLES     256
#define BMT_MAJOR       0
#define BMT_MINOR       0
#define BMT_BUGFIX      1
#define BUTTON_1        14
#define BUTTON_2        15


uint8_t even_odd_flag = 0;
uint8_t gps_buf[GPS_SAMPLES];
uint16_t data_buffer[NUM_SAMPLES];
static const uint8_t debounce_time = 50;
static bool buttton_pressed = false;
static int32_t alarm_id = 0;


sd_card_t * sd_if_init( void );
void sd_if_deinit( sd_card_t * sd_card );
void toggle_led( void );
void button_cb( uint gpio_no, uint32_t events );
int64_t enable_button( alarm_id_t alarm_id, void * user_data );

int main() {
    int idx = 0;
    int gps_idx = 0;
    unsigned int timestamp = 0;
    sd_card_t * storage;
    FRESULT f_result = FR_OK;
    FIL f_file;
    uint16_t * adc_data;

    stdio_init_all();
    
    if (cyw43_arch_init()) {
        printf("WiFi init failed");
        return -1;
    }
    
    gpio_init(BUTTON_1);
    gpio_pull_down(BUTTON_1);
    gpio_init(BUTTON_2);
    gpio_pull_down(BUTTON_2);
    
    gpio_set_irq_enabled_with_callback(BUTTON_1, GPIO_IRQ_LEVEL_HIGH, true, &button_cb);
    gpio_set_irq_enabled(BUTTON_2, GPIO_IRQ_LEVEL_HIGH, true);
  

    storage = sd_if_init();
    if ( NULL == storage ){
        printf( "Error initializing SD Card.\n") ;
        return -1;
    }

    /* Initialize the ADC hardware */
    adc_data = adc_collector_init();
    if ( NULL == adc_data ) {
        printf( "Error initializing ADC.\n");
        return -1;
    }

    /* Initialize GPS collector */
    gps_collector_init();

    const char* const filename = "bmt_test.log";
    f_result = f_open( &f_file, filename, FA_OPEN_APPEND | FA_WRITE );
    if ( FR_OK != f_result && FR_EXIST != f_result ) {
        printf( "f_open(%s) error: %s (%d)\n", filename, FRESULT_str(f_result), f_result );
    } else {
        if ( f_printf( &f_file, "BMT says Hello!\n" ) < 0 ) {
            printf("f_printf failed\n");
        }
    }

    f_result = f_close( & f_file );
    if ( FR_OK != f_result ) {
        printf( "f_close error: %s (%d)\n", FRESULT_str(f_result), f_result );
    }

    sd_if_deinit( storage );
    

    /* Start ADC/DMA transfer. */
    adc_collector_start_adc();
  
    printf( "Welcome to BMT v%d.%d.%d", BMT_MAJOR, BMT_MINOR, BMT_BUGFIX );
    while (true) {
        adc_collector_wait_for_new_data( adc_data );

        timestamp = to_ms_since_boot( get_absolute_time() );
        //TODO: Build travel data block.
        printf( "\nTIME: %u\n", timestamp );
        for (idx = 0; idx < NUM_SAMPLES; idx++ ) {
            data_buffer[idx] = adc_data[idx];
        }

        gps_idx = gps_collector_grab_data( gps_buf, GPS_SAMPLES );
        //TODO: Build GPS data block

        for( idx = 0; idx < gps_idx; idx++ ) {
            printf( "%c", gps_buf[idx] );
        }
     
        //for ( idx = 0; idx < NUM_SAMPLES; idx+=2 ) {
        //    printf( "%d 1: %03d | 2: %03d\n", idx/2, data_buffer[idx], data_buffer[idx+1] );
        //}

        toggle_led();             
    }
}




sd_card_t * sd_if_init( void )
{
    time_init();

    sd_card_t * sd_card = sd_get_by_num(0);
    FRESULT f_result = f_mount( &sd_card->fatfs, sd_card->pcName, 1 );

    if ( FR_OK != f_result ) {
        printf( "Error mounting: %s (%d)\n", FRESULT_str(f_result), f_result );
        return NULL;
    }

    return sd_card;
}

void sd_if_deinit( sd_card_t * sd_card )
{
    f_unmount( sd_card->pcName );
}

void toggle_led( void )
{
    static uint8_t led_flag = 0;

    if (led_flag) {
        led_flag = 0;
    } else {
        led_flag = 1;
    }

    //cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led_flag);   
}

void button_cb( uint gpio_no, uint32_t events )
{
    if ( buttton_pressed ) {
        cancel_alarm( alarm_id );
    } else {
        buttton_pressed = true;
        printf( "GPIO Button %d pressed.\n", gpio_no );
    }

    alarm_id = add_alarm_in_ms( debounce_time, enable_button, NULL, false );
}

int64_t enable_button( alarm_id_t alarm_id, void * user_data )
{
    buttton_pressed = false;
    return 0;
}