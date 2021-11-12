/* ADC1 Example
   This example code is in the Public Domain (or CC0 licensed, at your option.)
   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
#include <stdio.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/adc.h"
#include "driver/timer.h"
#include "esp_adc_cal.h"

#define DEFAULT_VREF    1100        //Use adc2_vref_to_gpio() to obtain a better estimate
#define NO_OF_SAMPLES   8           //Multisampling
#define TIMER_DIVIDER   (16)
#define S_MS_DIV        (1000)
#define TIMER_SCALE     (TIMER_BASE_CLK / TIMER_DIVIDER / S_MS_DIV )

static esp_adc_cal_characteristics_t *adc_chars;
static const adc_channel_t channel_front = ADC_CHANNEL_5;
static const adc_channel_t channel_back = ADC_CHANNEL_4; //GPIO34 if ADC1, GPIO14 if ADC2
static const adc_bits_width_t width = ADC_WIDTH_BIT_12;
static const adc_atten_t atten = ADC_ATTEN_DB_11;
static const adc_unit_t unit = ADC_UNIT_1;
volatile int tick = 0;
typedef struct {
    int timer_group;
    int timer_idx;
    int alarm_interval;
    bool auto_reload;
} example_timer_info_t;


static void check_efuse(void)
{
    //Check if TP is burned into eFuse
    if (esp_adc_cal_check_efuse(ESP_ADC_CAL_VAL_EFUSE_TP) == ESP_OK) {
        printf("eFuse Two Point: Supported\n");
    } else {
        printf("eFuse Two Point: NOT supported\n");
    }
    //Check Vref is burned into eFuse
    if (esp_adc_cal_check_efuse(ESP_ADC_CAL_VAL_EFUSE_VREF) == ESP_OK) {
        printf("eFuse Vref: Supported\n");
    } else {
        printf("eFuse Vref: NOT supported\n");
    }
}


static void print_char_val_type(esp_adc_cal_value_t val_type)
{
    if (val_type == ESP_ADC_CAL_VAL_EFUSE_TP) {
        printf("Characterized using Two Point Value\n");
    } else if (val_type == ESP_ADC_CAL_VAL_EFUSE_VREF) {
        printf("Characterized using eFuse Vref\n");
    } else {
        printf("Characterized using Default Vref\n");
    }
}

static bool IRAM_ATTR timer_group_isr_callback(void *args)
{
    BaseType_t high_task_awoken = pdFALSE;

    tick = 1;

    return high_task_awoken == pdTRUE; // return whether we need to yield at the end of ISR
}

static void timer_init_timer( int timer_interval_ms ) {

    int timer_group = TIMER_GROUP_0;
    int timer_no = TIMER_0;
        timer_config_t timer_config = {
        .divider = TIMER_DIVIDER,
        .counter_dir = TIMER_COUNT_UP,
        .counter_en = TIMER_PAUSE,
        .alarm_en = TIMER_ALARM_EN,
        .auto_reload = true,
    }; // default clock source is APB
    timer_init(timer_group, timer_no, &timer_config);

    timer_set_counter_value(timer_group, timer_no, 0);

    timer_set_alarm_value(timer_group, timer_no, timer_interval_ms * TIMER_SCALE);
    timer_enable_intr(timer_group, timer_no);
    example_timer_info_t *timer_info = calloc(1, sizeof(example_timer_info_t));
    timer_info->timer_group = 0;
    timer_info->timer_idx = 0;
    timer_info->auto_reload = true;
    timer_info->alarm_interval = timer_interval_ms;
    timer_isr_callback_add(timer_group, timer_no, timer_group_isr_callback, timer_info, 0);

    timer_start(timer_group, timer_no);

}


void app_main(void)
{

    // ADC1 CH4 & CH5 are used in BMT
    //Check if Two Point or Vref are burned into eFuse
    check_efuse();

    //Configure ADC
    if (unit == ADC_UNIT_1) {
        adc1_config_width(width);
        adc1_config_channel_atten(channel_front, atten);
        adc1_config_channel_atten(channel_back, atten);
    } else {
        printf( "Only use of ADC1 is permitted.\n");
        printf("test");
        exit(1);
    }

    //Characterize ADC
    adc_chars = calloc(1, sizeof(esp_adc_cal_characteristics_t));
    esp_adc_cal_value_t val_type = esp_adc_cal_characterize(unit, atten, width, DEFAULT_VREF, adc_chars);
    print_char_val_type(val_type);

    timer_init_timer( 1000 );

    //Continuously sample ADC1
    while (1) {
        if ( tick > 0) {
            tick = 0;
            uint32_t adc_front = 0;
            uint32_t adc_back = 0;
            //Multisampling
            for (int i = 0; i < NO_OF_SAMPLES; i++) {
                adc_front += adc1_get_raw((adc1_channel_t)channel_front);
                adc_back += adc1_get_raw((adc1_channel_t)channel_back);
            }
            adc_front /= NO_OF_SAMPLES;
            adc_back /= NO_OF_SAMPLES;
            //Convert adc_reading to voltage in mV
            uint32_t front_volt = esp_adc_cal_raw_to_voltage(adc_front, adc_chars);
            uint32_t back_volt = esp_adc_cal_raw_to_voltage(adc_back, adc_chars);
            printf("Front: Raw: %d\tVoltage: %dmV\n", adc_front, front_volt);
            printf("Back: Raw: %d\tVoltage: %dmV\n", adc_back, back_volt);

            
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}