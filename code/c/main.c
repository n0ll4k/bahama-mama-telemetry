/**
 * Bahama Mama Telemetry
 * by Frederik Krämer
 * 
 * 2023
 */
#include <stdint.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "pico/util/queue.h"
#include "pico/multicore.h"
#include "hardware/gpio.h"

#include "data_collector/data_collector.h"
#include "gps_collector/gps_collector.h"
#include "gps_collector/gps_fifo.h"
#include "adc_collector/adc_collector.h"
#include "sd_if/sd_if.h"


#define BMT_MAJOR           0
#define BMT_MINOR           0
#define BMT_BUGFIX          1

#define BTN_START_STOP      14
#define BTN_WIFI            15
#define QUEUE_WORK_LEVEL    24

enum app_state_e {
    state_init = 0x00,
    state_idle,
    state_start_file,
    state_start,
    state_meas,
    state_stop,
    state_stop_file,
    state_transfer 
};

queue_t core_queue;
static const uint8_t debounce_time = 50;
static bool buttton_pressed = false;
static int32_t alarm_id = 0;
enum app_state_e app_state = state_init;

void init_buttons( void );
void button_cb( uint gpio_no, uint32_t events );
int64_t enable_button( alarm_id_t alarm_id, void * user_data );

void core1_entry() 
{   
    sd_card_t * storage;
    queue_element_t element;
    
    storage = sd_if_init();
    if ( NULL == storage ){
        return;
    }

    while (1) {
        switch( app_state ) {
            case state_start_file:
                sd_if_open_new_file();
                printf( "Start file.\n");
                app_state = state_start;
                break;
            case state_meas:
            case state_stop:
                while (queue_try_remove(&core_queue, &element)) {
                    sd_if_write_to_file( &element, (sizeof(queue_element_t) ) );
                }
                break;
            case state_stop_file:
                sd_if_close_file();
                printf( "Stoping measurement.\n");
                app_state = state_idle;
                break;
            default:
                sleep_ms( 25 );
                break;
        }
    }

    /* We will not hit this. */
    sd_if_deinit( storage );
}


int main() {
    
 
    stdio_init_all();
    
    if (cyw43_arch_init()) {
        printf("WiFi init failed");
        return -1;
    }
    
    init_buttons();

    queue_init( &core_queue, sizeof(queue_element_t), 1024 );
  
    multicore_launch_core1(core1_entry);

    sleep_ms(2000);

    /* Initialize data collection. */
    if ( 0 != data_collector_init( &core_queue ) ) {
        printf( "Error initializing data collection.\n");
    }

    app_state = state_idle;

    /* Loop-Y-Loop */
    while (true) {
        switch( app_state ) {
            case state_meas:
                if ( 0 != data_collector_collect_and_push() ) {
                    printf( "Error during data collection.\n");
                }
                break;
            case state_stop:
                //adc_collector_stop_adc();
                data_collector_stop();
                app_state = state_stop_file;
                break;
            case state_start:
                //adc_collector_start_adc();
                data_collector_start();
                app_state = state_meas;
                break;
            case state_idle:
            case state_transfer:
            default:
                sleep_ms(25);
                break;
        }
        
    }
}


void button_cb( uint gpio_no, uint32_t events )
{   
    if ( buttton_pressed ) {
        cancel_alarm( alarm_id );
    } else {
        printf( "button pressed.\n");
        buttton_pressed = true;
        switch( gpio_no ) {
            case BTN_START_STOP:
                switch( app_state ) {
                    case state_idle:
                        printf( "Start meas.\n");
                        app_state = state_start_file;
                        break;
                    case state_meas:
                        printf( "Stop meas.\n");
                        app_state = state_stop;
                        break;
                    default:
                        break;
                }
                break;
            case BTN_WIFI:
                switch( app_state ) {
                    case state_idle:
                        app_state = state_transfer;
                        break;
                    case state_transfer:
                        app_state = state_idle;
                    default:
                        break;
                }
                break;
            default:
                break;
        }
    }

    alarm_id = add_alarm_in_ms( debounce_time, enable_button, NULL, false );
}

int64_t enable_button( alarm_id_t alarm_id, void * user_data )
{
    buttton_pressed = false;
    return 0;
}

void init_buttons( void )
{
    gpio_init(BTN_START_STOP);
    gpio_pull_down(BTN_START_STOP);
    gpio_init(BTN_WIFI);
    gpio_pull_down(BTN_WIFI);
    
    gpio_set_irq_enabled_with_callback(BTN_START_STOP, GPIO_IRQ_LEVEL_HIGH, true, &button_cb);
    gpio_set_irq_enabled(BTN_WIFI, GPIO_IRQ_LEVEL_HIGH, true);
}