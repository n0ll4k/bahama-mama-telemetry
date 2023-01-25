# Design

As KISS (keep it stupid simple) is one of my favorite design principles while designing embedded software the desin of this system leaned towards that.

Overall the goal is to have a system consisting of as many of the shelf parts as possible and also have a pretty simple software which is easily maintainable and expansible.

The following diagram shows the software components of the system.

![Software components](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/n0ll4k/bahama-mama-telemetry/main/docs/design/bmt_components.plantuml)

As the Raspberry Pi Pico is able to utilize two cores we will use these cores for different tasks. Therefore we have a good seperation of concerns within our software.

One part will be the collection of the raw data. This will be done on Core 0 and a data collector is utilized for this part. The goal is to utilize the DMA of the processor for most of the data transfers from the periphery to memory. As the Pico has 12 DMA channels that should be doable.

The data collector will configure and start the collection of data via the ADC and UART (for the GPS module). As the project progresses other sensor can be added to the data collector. Currently it is unknown if an internal timestamp is needed to synchronize all recorded data. This will be one of the open questions going into the project. This shall be answered after initial testing. Especially consindering there will be more then the current amount of sensors connected which need to be distinguished and synchronized.

After the data is collected from the periphery it will be put to the multicore FIFO which is part of the Pico SDK. To distinguish the different data types an identifier needs to be in front of the data.

Core 1 will be running the data composer. The composer only checks for new data from the multicore FIFO and handles the data storage to the uSD card. The composer checks which data shall be written to the storage and stores it accordingly to the defined formats.