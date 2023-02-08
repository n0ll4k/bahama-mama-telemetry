/**
 * Bahama Mama Telemetry
 * by Frederik Krämer
 * 
 * 2023
 */
#include <stdint.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "pico/util/queue.h"
#include "pico/multicore.h"
#include "hardware/gpio.h"

#include "f_util.h"
#include "ff.h"
#include "rtc.h"
#include "hw_config.h"

#include "data_collector/data_collector.h"
#include "gps_collector/gps_collector.h"
#include "gps_collector/gps_fifo.h"
#include "adc_collector/adc_collector.h"


#define BMT_MAJOR           0
#define BMT_MINOR           0
#define BMT_BUGFIX          1

#define BUTTON_1            14
#define BUTTON_2            15
#define QUEUE_WORK_LEVEL    24


queue_t core_queue;
static const uint8_t debounce_time = 50;
static bool buttton_pressed = false;
static int32_t alarm_id = 0;


sd_card_t * sd_if_init( void );
void sd_if_deinit( sd_card_t * sd_card );

void init_buttons( void );
void button_cb( uint gpio_no, uint32_t events );
int64_t enable_button( alarm_id_t alarm_id, void * user_data );

void core1_entry() 
{   
    int idx = 0;
    int queue_lvl = 0;
    uint32_t data[256];
    sd_card_t * storage;
    FRESULT f_result = FR_OK;
    FIL f_file;

    storage = sd_if_init();
    if ( NULL == storage ){
        printf( "Error initializing SD Card.\n") ;
        return;
    }

    const char* const filename = "bmt_test.log";
    f_result = f_open( &f_file, filename, FA_OPEN_APPEND | FA_WRITE );
    if ( FR_OK != f_result && FR_EXIST != f_result ) {
        printf( "f_open(%s) error: %s (%d)\n", filename, FRESULT_str(f_result), f_result );
    } 

    while (1) {
        queue_lvl = queue_get_level(&core_queue);
        if(  queue_lvl > QUEUE_WORK_LEVEL ) {
            for ( idx = 0; idx < queue_lvl; idx++ ) {
                queue_remove_blocking(&core_queue, (data+idx));
            }

            f_write( &f_file, data, (sizeof(uint32_t)*queue_lvl), NULL);
            f_sync( &f_file );
        }
    }

    /* We will not hit this. */
    f_result = f_close( & f_file );
    if ( FR_OK != f_result ) {
        printf( "f_close error: %s (%d)\n", FRESULT_str(f_result), f_result );
    }
    sd_if_deinit( storage );
}


int main() {
    int idx = 0;
 
    stdio_init_all();
    
    if (cyw43_arch_init()) {
        printf("WiFi init failed");
        return -1;
    }
    
    init_buttons();

    queue_init( &core_queue, sizeof(uint32_t), 256 );
  
    sleep_ms(1000);
    
    printf( "Welcome to BMT v%d.%d.%d\n", BMT_MAJOR, BMT_MINOR, BMT_BUGFIX );

   multicore_launch_core1(core1_entry);

   sleep_ms(1000);

    /* Initialize data collection. */
    if ( 0 != data_collector_init( &core_queue ) ) {
        printf( "Error initializing data collection.\n");
        return -1;
    }

    /* Grab data. */
    while (true) {
        if ( 0 != data_collector_collect_and_push() ) {
            printf( "Error during data collection.\n");
        }
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

void init_buttons( void )
{
    gpio_init(BUTTON_1);
    gpio_pull_down(BUTTON_1);
    gpio_init(BUTTON_2);
    gpio_pull_down(BUTTON_2);
    
    gpio_set_irq_enabled_with_callback(BUTTON_1, GPIO_IRQ_LEVEL_HIGH, true, &button_cb);
    gpio_set_irq_enabled(BUTTON_2, GPIO_IRQ_LEVEL_HIGH, true);
}