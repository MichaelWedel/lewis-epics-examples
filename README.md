Simple Lewis EPICS examples
===========================

This repository contains two examples for [Lewis](https://github.com/DMSC-Instrument-Data/lewis) simulators with an EPICS interface. The first
one simply adds an EPICS interface to the `SimulatedExampleMotor` from `lewis.examples`, while
the second one is a bit more special, it's a simulated pet that has to be kept alive via EPICS.

The features described here refer to Lewis [version 1.0.2](https://pypi.python.org/pypi/lewis/1.0.2), in the current master branch or newer
releases these might be different.

Installation
------------

Clone this repository:

    $ git clone https://github.com/MichaelWedel/lewis-epics-examples

Install the requirements (lewis version 1.0.2) via pip, preferably in a virtual environment:

    $ cd lewis-epics-examples
    $ pip install -r requirements.txt

Just as a warning, this installs pcaspy and thus needs a working EPICS-base installation).
That's it, everything is ready!

The motor
---------

To start the motor:

    $ lewis -a . -k devices epics_motor -- --prefix=Motor1:

The log output will give information about the PVs that are available. The simulation is very
simple, when the `Motor1:Tgt` is set, the motor will automatically change state from `idle` to
`moving`. This can be directly observed in `Motor1:Stat`, but of course also `Motor1:Pos`.

All actions will also be visible in the log, that is printed to `STDERR`.

It might be interesting to modify some internal parameters beyond the limits that EPICS allows,
for example the speed. The PV is limited between 0 and 10.

Kill the motor simulation by pressing `CTRL+c`, and start it again with the control server
activated:

    $ lewis -r localhost:10000 -a . -k devices epics_motor -- --prefix=Motor1:

This will start a control server that allows deep control of the simulation and the device via
the `lewis-control` script:

    $ lewis-control device speed 25

This sets the device speed to a value that is not achievable via EPICS. It's also possible to
obtain the documentation for the EPICS interface via the control server:

    $ lewis-control simulation device_documentation

Another interesting opportunity for testing is disconnecting the device:

    $ lewis-control simulation disconnect_device

That's about all there is to say about the motor, the general
[documentation](http://lewis.readthedocs.io/en/v1.0.2/), especially about the adapters and the
device writing guide contain more detailed information.

The pet
-------

This is a fun little example, it's a simulated pet in the computer that has certain needs that
must be satisfied. Start it up:

    $ lewis -r localhost -a . -k devices pet -- -p Pet:

Unlike other pets, it can only interact via EPICS! Start the simulation by naming the pet:

    $ caput Pet:name FooBar

The pet will slowly age and show general signs of decay (bored, hungry, ...) which need to be
counteracted. This examples profits from a faster simulation speed:

    $ lewis-control simulation speed 10
