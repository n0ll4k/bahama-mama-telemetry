#include "hardware/gpio.h"
#include "hardware/uart.h"
#include "hardware/irq.h"

#include "gps_fifo.h"

#define UART_ID         uart1
#define BAUD_RATE       9600
#define DATA_BITS       8
#define STOP_BITS       1
#define PARITY          UART_PARITY_NONE
#define UART_TX_PIN     8
#define UART_RX_PIN     9

void on_uart_rx( void );

void gps_collector_init( void )
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

int gps_collector_grab_data( uint8_t * buffer, uint16_t max_length )
{
    int index = 0;
    uint16_t data = gps_fifo_level();
    if ( data > max_length ) {
        data = max_length;
    }

    for ( index = 0; index < data; index++ ) {
        gps_fifo_pop(&buffer[index]);
    }

    return data;
}

// RX interrupt handler
void on_uart_rx() {
    while (uart_is_readable(UART_ID)) {
        uint8_t ch = uart_getc(UART_ID);
        
        gps_fifo_push( ch );
    }
}