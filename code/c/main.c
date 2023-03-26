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
#define BTN_START_STOP      1
#define BTN_WIFI            5
#define INPUT_LEN           2
#define STATE_LED_PIN       22
//---------------------------------------------------------------------------
enum app_state_e {
    state_init = 0x00,
    state_idle,
    state_start_file,
    state_start,
    state_meas,
    state_stop,
    state_stop_file,
    state_transfer,
    state_stop_transfer 
};

queue_t core_queue;
static const uint8_t debounce_time = 50;
static bool buttton_pressed = false;
static int32_t alarm_id = 0;
enum app_state_e app_state = state_init;
uint32_t input_array[INPUT_LEN] = {BTN_START_STOP, BTN_WIFI};
static bool input_states[INPUT_LEN] = {0, 0};
static bool led_blink_state = false;
const char *ap_name = "BahamaMamaTelemetry";
const char *password = "GetDrunkOnBMT";
//---------------------------------------------------------------------------
void sd_handling_core1( void );
void bttn_init( void );
bool rep_timer_callback( struct repeating_timer *timer);
bool debounce_start_bttn(void);
bool debounce_wifi_bttn(void);
void set_led_blink_state(bool state);
//---------------------------------------------------------------------------

/* Core0 Handling. */
int main() 
{
    struct repeating_timer timer;

    stdio_init_all();

    if (cyw43_arch_init()) {
        printf("failed to initialise\n");
        return 1;
    }
    cyw43_arch_enable_ap_mode(ap_name, password, CYW43_AUTH_WPA2_AES_PSK);

    gpio_init(STATE_LED_PIN);
    gpio_set_dir( STATE_LED_PIN, GPIO_OUT );

    bttn_init();
    add_repeating_timer_ms(-25, rep_timer_callback, NULL, &timer);

    queue_init( &core_queue, sizeof(queue_element_t), 1024 );

    multicore_launch_core1(sd_handling_core1);

    /* Initialize data collection. */
    if ( 0 != data_collector_init( &core_queue ) ) {
        return 1;
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
            case state_transfer:
                /* TODO: Run TCP Server and transfer data. */
                sleep_ms(25);
                break;
            case state_stop_transfer:
                set_led_blink_state( false );
                app_state = state_idle;
                break;
            case state_idle:
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
        printf("failed to initialize sd card.");
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

    /* We should never hit this. */
    sd_if_deinit( storage );
}

//---------------------------------------------------------------------------
bool rep_timer_callback( struct repeating_timer *timer)
{   
    static bool led_state = false;
    static uint32_t led_cnt = 20;
    if(debounce_start_bttn() ){
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
    }

    if( debounce_wifi_bttn() ) {
        switch( app_state ) {
            case state_idle:
                set_led_blink_state( true );
                app_state = state_transfer;
                break;
            case state_transfer:
                app_state = state_stop_transfer;
            default:
                break;
        }
    }

    if ( led_blink_state ) {
        led_cnt--;
        if (led_cnt == 0) {
            led_cnt = 20;
            if ( gpio_get( STATE_LED_PIN ) ){
                gpio_put( STATE_LED_PIN, 0);
            } else {
                gpio_put( STATE_LED_PIN, 1);
            }
        }
    }

    return true;
}

void bttn_init( void )
{
    gpio_init(BTN_START_STOP);
    gpio_set_dir( BTN_START_STOP, GPIO_IN );
    gpio_pull_up(BTN_START_STOP);

    gpio_init(BTN_WIFI);
    gpio_set_dir( BTN_WIFI, GPIO_IN) ;
    gpio_pull_up(BTN_WIFI);
}

bool debounce_start_bttn(void)
{
    static uint16_t bttn_state = 0;
    bttn_state = ( bttn_state << 1 ) | !gpio_get(BTN_START_STOP) | 0xe000;
    if ( bttn_state == 0xf000 ){
        return true;
    }
    return false;
}

bool debounce_wifi_bttn(void)
{
    static uint16_t bttn_state = 0;
    bttn_state = ( bttn_state << 1 ) | !gpio_get(BTN_WIFI) | 0xe000;
    if ( bttn_state == 0xf000 ){
        return true;
    }
    return false;
}

void set_led_blink_state(bool state)
{
    if ( state ) {
        led_blink_state = state;
    } else {
        led_blink_state = state;
        gpio_put( STATE_LED_PIN, 0);
    }
}