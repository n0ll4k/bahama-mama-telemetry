#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/adc.h"
#include "hardware/dma.h"

#include "adc_coll.h"

#define FORK_SENSOR     26
#define DAMPER_SENSOR   27
#define FORK_ADC_CHAN   0
#define DAMPER_ADC_CHAN 1
#define ADC_CHAN_MASK   ( 1 << FORK_ADC_CHAN ) | ( 1 << DAMPER_ADC_CHAN )


/*--------------------------------------------------------------------------------*/
bool flag;
int16_t sample_buffer_1[NUM_SAMPLES];
uint16_t sample_buffer_2[NUM_SAMPLES];
uint16_t * sample_pt = &sample_buffer_1[0];
dma_channel_config adc_sample_cfg;
dma_channel_config adc_ctrl_cfg;
adc_coll_data_t adc_collector_data = {
    .sample_channel = 0,
    .ctrl_channel = 0,
    .p_data = NULL
};


void adc_init_hw( void );
int dma_init_adc_channels( adc_coll_data_t * adc_data );

/*--------------------------------------------------------------------------------*/

adc_coll_data_t * adc_coll_init( void )
{
    adc_init_hw();

    /* Initialize DMA channels for ADC */
    if ( -1 == dma_init_adc_channels( &adc_collector_data) ) {
        //printf( "Error initializing DMA channels for ADC.\n");
        return NULL;
    }

    return &adc_collector_data;
}

void adc_coll_start_adc( void )
{
    dma_start_channel_mask((1u << adc_collector_data.sample_channel));
    adc_run(true) ;
}

void adc_coll_wait_for_new_data( adc_coll_data_t * adc_data )
{
        dma_channel_wait_for_finish_blocking( adc_data->sample_channel );

        if (flag) {
            flag = false;
            sample_pt = &sample_buffer_1[0];
            adc_data->p_data = &sample_buffer_2[0];
        } else {
            flag = true;
            sample_pt = &sample_buffer_2[0];
            adc_data->p_data = &sample_buffer_1[0];
        }
        
        dma_channel_start( adc_data->ctrl_channel );
}


/*--------------------------------------------------------------------------------*/

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

int dma_init_adc_channels( adc_coll_data_t * adc_data )
{
    adc_data->sample_channel = dma_claim_unused_channel( false );
    if ( -1 == adc_data->sample_channel ) {
        //printf( "Error grabbing ADC sample dma channel.");
        return -1;
    }

    adc_data->ctrl_channel = dma_claim_unused_channel( false );
    if ( -1 == adc_data->ctrl_channel ) {
        //printf( "Error grabbing ADC ctrl DMA channel.");
        return -1;
    }

    adc_sample_cfg = dma_channel_get_default_config( adc_data->sample_channel );
    adc_ctrl_cfg = dma_channel_get_default_config ( adc_data->ctrl_channel );

    /* Configure ADC sample channel */
    channel_config_set_transfer_data_size( &adc_sample_cfg, DMA_SIZE_16 );  /* 16-Bit transfer size. */
    channel_config_set_read_increment( &adc_sample_cfg, false );            /* Read from constant address. */
    channel_config_set_write_increment( &adc_sample_cfg, true );            /* Write to incrementing address. */
    channel_config_set_dreq ( &adc_sample_cfg, DREQ_ADC );                  /* Set pace to ADC pace. */
    dma_channel_configure( 
        adc_data->sample_channel,   /* Channel to configure */
        &adc_sample_cfg,            /* Channel config */
        sample_buffer_1,            /* Write address */
        &adc_hw->fifo,              /* Read address */
        NUM_SAMPLES,                /* Number of samples */
        false                       /* Don't start immediately. */
    );

    /* Configure ADC control channel */
    channel_config_set_transfer_data_size( &adc_ctrl_cfg, DMA_SIZE_32 );    /* 32-Bit transfer size. */
    channel_config_set_read_increment( &adc_ctrl_cfg, false );              /* Read from constant address. */
    channel_config_set_write_increment( &adc_ctrl_cfg, false );             /* Write to constant address. */
    channel_config_set_chain_to( &adc_ctrl_cfg, adc_data->sample_channel ); /* Chain to ADC channel. */
    dma_channel_configure(
        adc_data->ctrl_channel,                             /* Channel to configure */
        &adc_ctrl_cfg,                                      /* Channel config */
        &dma_hw->ch[adc_data->sample_channel].write_addr,   /* Write address */
        &sample_pt,                                         /* Read address */
        1,                                                  /* Number of transfers, we only need one address transfer. */
        false                                               /* Don't start immediately .*/
    );

    return 0;
}