#include <stdio.h>
#include <string.h>

#include "sd_if.h"

#define INDEX_LEN           2
#define MAX_FILENAME_LEN    16

FIL current_file;

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

int sd_if_close_file( void ) 
{
    FRESULT file_result = FR_OK;
    f_sync( &current_file );
    
    file_result = f_close( &current_file );
    if ( FR_OK != file_result ) {
        return -1;
    }
    return 0;
}

int sd_if_open_new_file( void )
{
    uint8_t buffer[INDEX_LEN];
    char filename[MAX_FILENAME_LEN];
    uint file_len = 0;
    uint16_t file_index = 0;
    FRESULT file_result = FR_OK;
    FIL index_file;

    memset( filename, 0x00, MAX_FILENAME_LEN);

    /* Get current index from index file. */
    file_result = f_open( &index_file, "FILE_INDEX", FA_OPEN_EXISTING | FA_READ);
    if ( ( FR_OK == file_result ) || 
         ( FR_EXIST == file_result ) ){
        f_read( &index_file, buffer, INDEX_LEN, &file_len );
        if ( INDEX_LEN == file_len ) {
            file_index = ( ( buffer[0] << 8 ) | buffer[1] );
            file_index += 1;
        }
    }
    f_close( &index_file);

    /* Write next index to index file. */
    file_result = f_open( &index_file, "FILE_INDEX", FA_OPEN_ALWAYS | FA_WRITE);
    if ( FR_OK == file_result ){
        f_lseek( &index_file, 0 );
        buffer[0] = ( ( file_index & 0xFF00 ) >> 8 );
        buffer[1] = ( file_index & 0x00FF );
        f_write( &index_file, buffer, INDEX_LEN, &file_len );
        f_sync( &index_file );
    } else {
        return -1;
    }
    f_close( &index_file );

    /* Open data file */
    sprintf( filename, "bmt-%05u.log", file_index );
    file_result = f_open( &current_file, filename, FA_OPEN_APPEND | FA_WRITE );
    if ( FR_OK != file_result && FR_EXIST != file_result ) {
        return -1;
    } 

    return 0;
}

int sd_if_write_to_file( void * buffer, uint32_t buffer_length )
{
    int written_length = 0;
    if ( FR_OK != f_write( &current_file, buffer, buffer_length, &written_length) ) {
        written_length = -1;
    }
    //f_sync( &current_file );

    return written_length;
}