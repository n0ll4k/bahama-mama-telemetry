cmake_minimum_required(VERSION 3.13)

set(PICO_SDK_PATH "/Users/n0ll4k/Code/00_sdk/pico-sdk")
set(PICO_EXTRAS_PATH "/Users/n0ll4k/Code/00_sdk/pico-extras")

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)
# Pull in optional extras
include(pico_extras_import_optional.cmake)

# Set board
set(PICO_BOARD pico_w)

# Set project
project(bahama_mama_telemetry C CXX ASM)


set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

add_executable(bmt
    main.c
    hw_config.c
    gps_collector/gps_fifo.c
    gps_collector/gps_collector.c
    adc_collector/adc_collector.c
    data_collector/data_collector.c
    sd_if/sd_if.c
)

target_include_directories(bmt PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/..
        )

add_subdirectory(no-OS-FatFS-SD-SPI-RPi-Pico/FatFs_SPI build)

target_link_libraries(bmt
        pico_stdlib                 # for core functionality
        hardware_adc                # ADC to read potentiometers 
        hardware_dma                # DMA to transfer data.
        hardware_uart               # GPS Data
        FatFs_SPI                   # SD Card
        pico_multicore
    )
pico_enable_stdio_usb(bmt 1)
pico_enable_stdio_uart(bmt 0)

pico_add_extra_outputs(bmt) 