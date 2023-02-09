#ifndef _SD_IF_H
#define _SD_IF_H

#include <stdint.h>

#include "f_util.h"
#include "ff.h"
#include "rtc.h"
#include "hw_config.h"

sd_card_t * sd_if_init( void );
void sd_if_deinit( sd_card_t * sd_card );
int sd_if_close_file( void);
int sd_if_open_new_file( void );
int sd_if_write_to_file( void * buffer, uint32_t buffer_length );


#endif