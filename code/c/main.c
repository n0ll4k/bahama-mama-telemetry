/**
 * Bahama Mama Telemetry
 * 
 * A simple approach to a MTB telemetry system for suspension analysis. * 
 * by Frederik Krämer
 * 
 * 2023
 */
//---------------------------------------------------------------------------
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
//---------------------------------------------------------------------------
#define BMT_MAJOR           0
#define BMT_MINOR           0
#define BMT_BUGFIX          1
#define BTN_START_STOP      14
#define BTN_WIFI            15
#define QUEUE_WORK_LEVEL    24
#define STATE_LED_PIN       10
//---------------------------------------------------------------------------
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
//---------------------------------------------------------------------------
void sd_handling_core1( void );
void bttn_init( void );
void bttn_cb( uint gpio_no, uint32_t events );
int64_t bttn_enable( alarm_id_t alarm_id, void * user_data );
//---------------------------------------------------------------------------

/* Core0 Handling. */
int main() {
    stdio_init_all();
    if (cyw43_arch_init()) {
        return -1;
    }

    gpio_init(STATE_LED_PIN);
    gpio_set_dir( STATE_LED_PIN, GPIO_OUT );
    
    bttn_init();

    queue_init( &core_queue, sizeof(queue_element_t), 1024 );
  
    multicore_launch_core1(sd_handling_core1);

    sleep_ms(2000);

    /* Initialize data collection. */
    if ( 0 != data_collector_init( &core_queue ) ) {
        return -1;
    }

    app_state = state_idle;

    /* Loop-Y-Loop */
    while (true) {
        switch( app_state ) {
            case state_meas:
                data_collector_collect_and_push();
                break;
            case state_stop:
                data_collector_stop();
                app_state = state_stop_file;
                break;
            case state_start:
                data_collector_start();
                gpio_put(STATE_LED_PIN, 1);
                app_state = state_meas;
                break;
            case state_idle:
            case state_transfer:
            default:
                gpio_put(STATE_LED_PIN, 0);
                sleep_ms(25);
                break;
        }
        
    }
}

/* Core1 Handling. */
void sd_handling_core1(void) 
{   
    sd_card_t * storage;
    queue_element_t element;
    
    storage = sd_if_init();
    if ( NULL == storage ){
        return;
    }

    /* Loop-Y-Loop */
    while (true) {
        switch( app_state ) {
            case state_start_file:
                sd_if_open_new_file();
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

//---------------------------------------------------------------------------
void bttn_cb( uint gpio_no, uint32_t events )
{   
    if ( buttton_pressed ) {
        cancel_alarm( alarm_id );
    } else {
        buttton_pressed = true;
        switch( gpio_no ) {
            case BTN_START_STOP:
                switch( app_state ) {
                    case state_idle:
                        app_state = state_start_file;
                        break;
                    case state_meas:
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

    alarm_id = add_alarm_in_ms( debounce_time, bttn_enable, NULL, false );
}

int64_t bttn_enable( alarm_id_t alarm_id, void * user_data )
{
    buttton_pressed = false;
    return 0;
}

void bttn_init( void )
{
    gpio_init(BTN_START_STOP);
    gpio_pull_down(BTN_START_STOP);
    gpio_init(BTN_WIFI);
    gpio_pull_down(BTN_WIFI);
    
    gpio_set_irq_enabled_with_callback(BTN_START_STOP, GPIO_IRQ_LEVEL_HIGH, true, &bttn_cb);
    gpio_set_irq_enabled(BTN_WIFI, GPIO_IRQ_LEVEL_HIGH, true);
}