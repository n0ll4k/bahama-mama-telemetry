/**
 * Bahama Mama Telemetry
 * by Frederik Krämer
 * 
 * 2023
 */

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/gpio.h"
#include "hardware/adc.h"
#include "hardware/dma.h"
#include "hardware/uart.h"
#include "hardware/irq.h"

#include "gps_coll/gps_fifo.h"



#define FORK_SENSOR     26
#define DAMPER_SENSOR   27
#define FORK_ADC_CHAN   0
#define DAMPER_ADC_CHAN 1
#define ADC_CHAN_MASK   ( 1 << FORK_ADC_CHAN ) | ( 1 << DAMPER_ADC_CHAN )
#define NUM_SAMPLES     1000
#define GPS_SAMPLES     256

#define UART_ID         uart1
#define BAUD_RATE       9600
#define DATA_BITS       8
#define STOP_BITS       1
#define PARITY          UART_PARITY_NONE
#define UART_TX_PIN     8
#define UART_RX_PIN     9




int adc_sample_chan = 0;
int adc_ctrl_chan = 0;
uint8_t even_odd_flag = 0;
uint8_t uart_buf[GPS_SAMPLES];
uint16_t sample_buffer_1[NUM_SAMPLES];
uint16_t sample_buffer_2[NUM_SAMPLES];
uint16_t data_buffer[NUM_SAMPLES];
uint16_t * sample_pt = &sample_buffer_1[0];
uint16_t * data_pt = &sample_buffer_1[0];
dma_channel_config adc_sample_cfg;
dma_channel_config adc_ctrl_cfg;

void adc_init_hw( void );
int dma_init_adc_channels( void );
void uart_init_hw( void );
void on_uart_rx( void );


int main() {
    int idx = 0;
    unsigned int timestamp = 0;
    stdio_init_all();
    
    if (cyw43_arch_init()) {
        printf("WiFi init failed");
        return -1;
    }

    /* Initialize the ADC hardware */
    adc_init_hw();

    /* Initialize DMA channels for ADC */
    if ( -1 == dma_init_adc_channels() ) {
        printf( "Error initializing DMA channels for ADC.\n");
        return -1;
    }

    uart_init_hw();

    /* Start ADC/DMA transfer. */
    dma_start_channel_mask((1u << adc_sample_chan)) ;
    adc_run(true) ;

    while (true) {
        dma_channel_wait_for_finish_blocking( adc_sample_chan );

        if (even_odd_flag) {
            even_odd_flag = 0;
            sample_pt = &sample_buffer_1[0];
            data_pt = &sample_buffer_2[0];
        } else {
            even_odd_flag = 1;
            sample_pt = &sample_buffer_2[0];
            data_pt = &sample_buffer_1[0];
        }
        
        dma_channel_start( adc_ctrl_chan );

        timestamp = time_us_32();
        
        printf( "\nTIME: %u\n", timestamp );

        while( gps_fifo_level() ) {
            uint8_t ch = 0;
            gps_fifo_pop( &ch );
            printf( "%c", ch );
        }
        for (idx = 0; idx < NUM_SAMPLES; idx++ ) {
            data_buffer[idx] = data_pt[idx];
        }
     
        //for ( idx = 0; idx < NUM_SAMPLES; idx+=2 ) {
        //    printf( "%d 1: %03d | 2: %03d\n", idx/2, data_buffer[idx], data_buffer[idx+1] );
        //}
        
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, even_odd_flag);        
    }
}


void adc_init_hw( void )
{
    adc_init();

    adc_gpio_init(FORK_SENSOR);
    adc_gpio_init(DAMPER_SENSOR);

    adc_select_input(FORK_ADC_CHAN);

    adc_set_round_robin( ADC_CHAN_MASK );

    adc_fifo_setup(
        true,   /* Write each adc conversion to the FIFO. */
        true,   /* Enable DMA data request. */
        2,      /* DREQ asserted when at least 2 samples are present (both channels are read). */
        false,  /* We won't have the ERR bit for now. */
        false   /* Don't shift bytes we want the full 12-Bit for now. */
    );

    /* 
     * Divisor of 0 results in Full speed. 1000Hz is the goal for data acquisition.
     * As the read of 2 channels is done we need to configure the ADC Clock to 2000Hz.
     * 48000000/2000 = 24000
     */
    adc_set_clkdiv( 24000 );
}

int dma_init_adc_channels( void )
{
    adc_sample_chan = dma_claim_unused_channel( false );
    if ( -1 == adc_sample_chan ) {
        printf( "Error grabbing ADC sample dma channel.");
        return -1;
    }

    adc_ctrl_chan = dma_claim_unused_channel( false );
    if ( -1 == adc_ctrl_chan ) {
        printf( "Error grabbing ADC ctrl DMA channel.");
        return -1;
    }

    adc_sample_cfg = dma_channel_get_default_config( adc_sample_chan );
    adc_ctrl_cfg = dma_channel_get_default_config ( adc_ctrl_chan );

    /* Configure ADC sample channel */
    channel_config_set_transfer_data_size( &adc_sample_cfg, DMA_SIZE_16 );  /* 16-Bit transfer size. */
    channel_config_set_read_increment( &adc_sample_cfg, false );            /* Read from constant address. */
    channel_config_set_write_increment( &adc_sample_cfg, true );            /* Write to incrementing address. */
    channel_config_set_dreq ( &adc_sample_cfg, DREQ_ADC );                  /* Set pace to ADC pace. */
    dma_channel_configure( 
        adc_sample_chan,    /* Channel to configure */
        &adc_sample_cfg,    /* Channel config */
        sample_buffer_1,    /* Write address */
        &adc_hw->fifo,      /* Read address */
        NUM_SAMPLES,        /* Number of samples */
        false               /* Don't start immediately. */
    );

    /* Configure ADC control channel */
    channel_config_set_transfer_data_size( &adc_ctrl_cfg, DMA_SIZE_32 );    /* 32-Bit transfer size. */
    channel_config_set_read_increment( &adc_ctrl_cfg, false );              /* Read from constant address. */
    channel_config_set_write_increment( &adc_ctrl_cfg, false );             /* Write to constant address. */
    channel_config_set_chain_to( &adc_ctrl_cfg, adc_sample_chan );          /* Chain to ADC channel. */
    dma_channel_configure(
        adc_ctrl_chan,                              /* Channel to configure */
        &adc_ctrl_cfg,                              /* Channel config */
        &dma_hw->ch[adc_sample_chan].write_addr,    /* Write address */
        &sample_pt,                                 /* Read address */
        1,                                          /* Number of transfers, we only need one address transfer. */
        false                                       /* Don't start immediately .*/
    );

    return 0;
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