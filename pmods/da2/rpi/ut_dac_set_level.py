#!/usr/bin/env python
"""
Stripped down Digilent PMOD DA3 demonstration using the SPI device on Raspberry Pi

Two options : explicitly using the LDAC output/not.

Adam Stephen.
"""

import typer

"""-----------------------------------------------------------"""

# Linux Kernel SPI device driver references.
# Google("linux kernel spi device driver API")
# 
# https://www.kernel.org/doc/html/v4.14/driver-api/spi.html
# 
# Described as usual (full duplex clocked COPI,CIPO with chip select)
# chip select normally active low.  Optional interrupt.
# Linux assumes it will be the controller.
#
# One device model is abstracted via a controller represented by a controller struct
# and SPI devices are linked to this object as children.
#
# The altenative models the protocol which allows queues of SPI messages to be
# created and processed - typically asynchronously though synchronous wrappers
# can be managed.  Each message is built out of spi_transfer objects which 
# encompass the full duplex communication exchange.
#
# Options depend on chipset implementation (from basic GPIO to complex DMA engines)
# For performance optimisation there are routes to managing the buffer overhead
# and kernel/user space split.  Concepts such as kworkers and message pumps
# locks, queues and suchlike implement these alternatives.
#
# For multiple devices sharing comms lines support for an array of chip select
# lines is provided.  This does permit different devices to use alternative 
# clock rates and hence there is the possibility to multiplex use of the shared
# clock and data lines.
#
# This suggests we could control the dual DA2 channels using the two exposed 
# SPI subdevices on the raspberry pi from the linux perspective.  The limitation
# is that the common chip select on the DA2 breakout board will not permit
# separation of the two DAC registers.
#
#
#
# import necessary modules
#
# SPI communication
# https://pypi.org/project/spidev/
#
# Options to control CS etc.
# Output interface includes
#
# writebytes(list)
#
# writebytes2(list) : for lists of arbitrary sizes : auto chunking
# if the list exceeds the kernel module buffer size in /sys/module/spidev/parameters/bufsiz
#
# writebytes2 also automatically handles numpy byte arrays natively according to 
# python buffer protocol https://docs.python.org/3/c-api/buffer.html
#
# xfer(list, [speed, delay, bits_per_word]) performs "SPI transaction where chip select
# needs to be released/reactivated betweeen blocks" (but definition of blocks is ambiguous)
#
# xfer2(same API as xfer) : requires chip select to be held active between blocks active between blocks
# xfer3(as xfer2) : as xfer2 but with the buffer chunking facility
#
# TODO: investigate the differences and record the digital IO timeseries (can document using
# the javascript plotting library which is bundled with a tool seen recently for ipynb ??)
import spidev
# timing
import time
# GPIO
import RPi.GPIO as GPIO
# cli
import sys

import pdb
"""-----------------------------------------------------------"""

# SPI connection parameters
SPI_port = 0
CS_pin = 1
spi_clock_speed = int(4e06)   # spi clock frequency in Hz
spi_clock_speed = int(1e06)   # spi clock frequency in Hz
#spi_clock_speed = int(1e04)   # spi clock frequency in Hz

# GPIO LDAC pin using GPIO.BOARD (1..40) numbering
LDAC_pin = 11
CS_GPIO_PIN = 26
CS_GPIO_PIN = 11

# DAC bits and range
dac_bits = 12
dac_bits = 16
dac_bits = 12
dac_range = (2**dac_bits) -  2
dac_range = (2**(dac_bits)) -  200
dac_steps = 100
dac_step = int(dac_range/dac_steps)

"""-----------------------------------------------------------"""

class PmodSpiDev:
    def __init__(self, 
                SPI_port = SPI_port,
                CS_pin = CS_pin,
                spi_clock_speed = spi_clock_speed,
                spi_mode = 0b11):
        self.SPI_port = SPI_port
        self.CS_pin = CS_pin
        self.spi_clock_speed = spi_clock_speed
        self.spi_mode = spi_mode
        self.setup()

    def setup(self):
        self.spi = spidev.SpiDev()
        self.spi.open(self.SPI_port, self.CS_pin)
        self.spi.max_speed_hz = self.spi_clock_speed
        self.spi.mode = self.spi_mode

from enum import Enum

class XferMode(Enum):
    XFER1 = 1
    XFER2 = 2
    XFER3 = 3

class WaveformPattern(Enum):
    LEVELS = 1
    RAMP = 2
    SINE = 3
    TRIANGULAR = 4


class DA2:
    def __init__(self, 
                SPI_port = SPI_port,
                CS_pin = CS_pin,
                spi_clock_speed = spi_clock_speed,
                spi_mode = 0b11):
        self.pmod = PmodSpiDev(SPI_port, CS_pin, spi_clock_speed,spi_mode)
        self.spi = self.pmod.spi

    def prepare_buffer(self, values):
        """TODO: potentially make more efficient."""
        self.buffer = []
        for v in values:
            highbyte = v >> 8
            lowbyte = v & 0xFF
            self.buffer.extend([highbyte, lowbyte])
        
    def loop(self, iterations = 0, type = None, mode = XferMode.XFER1):
        """iterations 0 = forever. Rudimentary caching of levels/ramp/sinusoids""" 
        if type is not None:
            if type == WaveformPattern.LEVELS: self.set_levels(self.levels)
            if type == WaveformPattern.RAMP: self.set_ramp(ramp = self.ramp)
            # TODO: implement SINE/TRIANGULAR
        i = 0
        while (i < iterations) and (iterations > 0):
            if mode == XferMode.XFER1: self.xfer()
            if mode == XferMode.XFER2: self.xfer2()
            if mode == XferMode.XFER3: self.xfer3()
            i+=1

    def set_levels(self, levels):
        self.levels = levels
        self.prepare_buffer(levels)
    
    def set_ramp(self, start = 0, end = 4096, delta = 1, ramp = None):
        if ramp is not None:
            self.ramp = ramp
        else:
            self.ramp = list(range(int(start), int(end), int(delta)))
        self.prepare_buffer(self.ramp)

    def xfer(self, values = None):
        if values is not None:
            self.prepare_buffer(values)
        self.spi.xfer(self.buffer)

    def xfer2(self, values = None):
        if values is not None:
            self.prepare_buffer(values)
        self.spi.xfer2(self.buffer)
    
    def xfer3(self, values):
        if values is not None:
            self.prepare_buffer(values)
        self.spi.xfer3(self.buffer)

    def close(self):
        self.spi.close()

from itertools import chain

def debug_delay(delay = False, duration = 0.1):
    if delay:
        time.sleep(duration)


def test_suite_a(delta_t = 0.1):
    dac = DA2()
    for value in [2**i for i in range(0,12)]:
        print("Set level output to %d" % value)
        dac.set_levels([0,4095])
        dac.loop(iterations = 0, type = None, mode = XferMode.XFER1)
        time.sleep(delta_t)

# typer CLI support for development

app = typer.Typer()

@app.command()
def levels(maxbits: int = 12, iterations: int = 1, loop_delay: float = 0.1, value_delay: float = 1.0):
    dac = DA2()
    for i in range(0, iterations):
        for value in [2**i for i in range(0, maxbits)]:
            print("Set level output to %d" % value)
            dac.set_levels([value - 1])
            dac.loop(iterations, type = WaveformPattern.LEVELS, mode = XferMode.XFER1)
            time.sleep(value_delay)
        time.sleep(loop_delay)



if __name__ == '__main__':
    #debug = True
    #duration = 1.0
    #test_suite_a()
    app()