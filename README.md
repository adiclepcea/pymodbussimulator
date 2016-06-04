# pymodbussimulator - Multiple client simulator for ModBus

## Purpose

This tool should simulate en entire bus of RTU modbus clients.

## Description

You should put all clients to be simulated inside config.yaml. There is allready a config.yaml showing a two slaves bus. The tests were made for holding registers only. There is functionality coded in for coils or input registers or discrete inputs, but I did not tested it yet.

##Why a new modbus in Python

First of all, this is only intended for testing a modbus server. Right now, it only has the functionality I need.
The reason I've decided to implement a new solution instead of using the allready implemented (and great solution) named pymodbus, is that I need to respond to several addresses, not only one. As far as I saw, pymodbus does not do that.
Otherwise pymodbus is a much more complete and tested solution.

##Tools used

You will need to install both [PySerial](https://github.com/pyserial) and [PyYaml](http://pyyaml.org/) for the application to work.
* PySerial is used for communication with the 485 bus
* PyYaml is used to read the configuration (config.yaml) for the slaves to simulate.

You will need to have both of them installed and usable in your system before using _pymodbussimulator_

##How to use it

Clone it locally:

```
git clone https://github.com/adiclepcea/pymodbussimulator.git
```

and go into the pymodbussimulator directory:

```
cd SensInventory/server/pymodbussimulator
```

and run:

```
python multiplemodbusslaves.py
```

To configure the slaves you need to simulate, you should edit the _config.yaml_ file. The fields are self describing so it should not be a problem to understand what each one does. As it is now, the config file simulates two slaves with holding registers and coils.

##What does it know

Until now pymodbus simulator can simulate slaves for reading coils, inputs, input-discrete and holding registers.
I should also respond correctly to writing single registers requests. But since I do not need that, I did not test it thouroughly.

Perhaps, if I need to implement more capabilities, I will do it, but for now I don't.

