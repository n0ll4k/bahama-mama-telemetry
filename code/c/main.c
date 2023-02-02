/**
 * Bahama Mama Telemetry
 * by Frederik Krämer
 * 
 * 2023
 */

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/gpio.h"

#include "hardware/uart.h"
#include "hardware/irq.h"
#include "f_util.h"
#include "ff.h"
#include "rtc.h"
#include "hw_config.h"

#include "adc_coll/adc_coll.h"
#include "gps_coll/gps_fifo.h"






#define GPS_SAMPLES     256

#define UART_ID         uart1
#define BAUD_RATE       9600
#define DATA_BITS       8
#define STOP_BITS       1
#define PARITY          UART_PARITY_NONE
#define UART_TX_PIN     8
#define UART_RX_PIN     9


uint8_t even_odd_flag = 0;
uint8_t uart_buf[GPS_SAMPLES];
uint16_t data_buffer[NUM_SAMPLES];



void uart_init_hw( void );
void on_uart_rx( void );
sd_card_t * sd_if_init( void );
void sd_if_deinit( sd_card_t * sd_card );

int main() {
    int idx = 0;
    unsigned int timestamp = 0;
    sd_card_t * storage;
    FRESULT f_result = FR_OK;
    FIL f_file;
    adc_coll_data_t * adc_data;

    stdio_init_all();
    
    if (cyw43_arch_init()) {
        printf("WiFi init failed");
        return -1;
    }

    storage = sd_if_init();
    if ( NULL == storage ){
        printf( "Error initializing SD Card.\n") ;
        return -1;
    }

    /* Initialize the ADC hardware */
    adc_data = adc_coll_init();
    if ( NULL == adc_data ) {
        printf( "Error initializing ADC.\n");
        return -1;
    }

    /* Initialize UART HW */
    uart_init_hw();

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
    adc_coll_start_adc();

    while (true) {
        adc_coll_wait_for_new_data( adc_data );

        timestamp = time_us_32();
        
        printf( "\nTIME: %u\n", timestamp );

        while( gps_fifo_level() ) {
            uint8_t ch = 0;
            gps_fifo_pop( &ch );
            printf( "%c", ch );
        }
        for (idx = 0; idx < NUM_SAMPLES; idx++ ) {
            data_buffer[idx] = adc_data->p_data[idx];
        }
     
        //for ( idx = 0; idx < NUM_SAMPLES; idx+=2 ) {
        //    printf( "%d 1: %03d | 2: %03d\n", idx/2, data_buffer[idx], data_buffer[idx+1] );
        //}
        
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, even_odd_flag);        
    }
}




void uart_init_hw( void )
{
    uart_init(UART_ID, 9600);
    gpio_set_function( UART_TX_PIN, GPIO_FUNC_UART );
    gpio_set_function( UART_RX_PIN, GPIO_FUNC_UART );

    uart_set_hw_flow(UART_ID, false, false);
    uart_set_format(UART_ID, DATA_BITS, STOP_BITS, PARITY);

    uart_set_fifo_enabled(UART_ID, false);
    
    irq_set_exclusive_handler(UART1_IRQ, on_uart_rx);
    irq_set_enabled(UART1_IRQ, true);

    uart_set_irq_enables(UART_ID, true, false);
}

// RX interrupt handler
void on_uart_rx() {
    while (uart_is_readable(UART_ID)) {
        uint8_t ch = uart_getc(UART_ID);
        
        gps_fifo_push( ch );
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