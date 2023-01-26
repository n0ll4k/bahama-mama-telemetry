cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(bahama_mama_telemetry C CXX ASM)


set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

set(PICO_BOARD pico_w)

pico_sdk_init()

add_executable(bmt
    main.c
)
target_link_libraries(bmt
        pico_stdlib             # for core functionality
        pico_cyw43_arch_none    # we need Wifi to access the GPIO, but we don't need anything else
        hardware_adc            # ADC to read potentiometers 
        hardware_dma            # DMA to transfer data.
    )
pico_enable_stdio_usb(bmt 1)
pico_enable_stdio_uart(bmt 0)

pico_add_extra_outputs(bmt) 