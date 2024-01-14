#!/usr/bin/env python
"""
Stripped down Digilent PMOD DA3 demonstration using the SPI device on Raspberry Pi

Two options : explicitly using the LDAC output/not.

Adam Stephen.
"""

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
spi_clock_speed = int(1e04)   # spi clock frequency in Hz

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

class DA3:
    def __init__(self, 
                SPI_port = SPI_port,
                CS_pin = CS_pin,
                spi_clock_speed = spi_clock_speed,
                LDAC_pin = LDAC_pin,
                use_LDAC = False):
        self.SPI_port = SPI_port
        self.CS_pin = CS_pin
        self.spi_clock_speed = spi_clock_speed
        self.LDAC_pin = LDAC_pin
        self.use_LDAC = use_LDAC

    def setup(self):
        self.dac = spidev.SpiDev()
        self.dac.open(SPI_port, CS_pin)
        self.dac.max_speed_hz = self.spi_clock_speed
        # SPI mode 0 [CPOL|CPHA]
        # DA3 self.dac.mode = 0b00
        # DA2
        self.dac.mode = 0b11
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.LDAC_pin,GPIO.OUT)
        #GPIO.setup(self.LDAC_pin,GPIO.OUT)

    def output_data(self, value):
        """
        Output data to the DA3.
        According to use_LDAC with or without the LDAC line drive.
        Note that 
            dac.writebytes does not manage CS line
            dac.xfer does manage the CS line
        """

        # get high byte
        highbyte = value >> 8
        # get low byte
        lowbyte = value & 0xFF
        
#        pdb.set_trace()

        if self.use_LDAC:
            GPIO.output(self.LDAC_pin,True)
        else:
            GPIO.output(self.LDAC_pin, False)


        # send both bytes
        #self.dac.writebytes([highbyte, lowbyte])
        self.dac.xfer([highbyte, lowbyte])

        if self.use_LDAC:
            GPIO.output(self.LDAC_pin, False)
            GPIO.output(self.LDAC_pin, True)

    def xfer2(self, values):
        self.dac.xfer2(values)

    def xfer3(self, values):
        self.dac.xfer3(values)

    def close(self):
        self.dac.close()

from itertools import chain

def debug_delay(delay = False, duration = 0.1):
    if delay:
        time.sleep(duration)

if __name__ == '__main__':
#    pdb.set_trace()
    debug = True
    duration = 1.0
    ldacs = [DA3(use_LDAC = False), DA3(use_LDAC = True)]
    ldacs = [DA3(use_LDAC = False)]
    #ldacs = [ DA3(use_LDAC = True)]

    # TODO: add a user interface (or more than one)
    send_vals = False
    send_dvals = False
    ramp_up = False
    ramp_down = False
    block_output2 = True
    loop = True
    while True:
        for DAC in ldacs:
            DAC.setup()
            vals = []
            dvals = []
            smallbuf = []
            ismall = 0
            largebuf = []
            ilarge = 0
            #for j in chain(range(0,dac_range,dac_step), range(0,dac_range, ), range(dac_range, 0, -1*dac_step)):
            #for j in range(0,int(0.5*dac_range),dac_step):
            dac_range = 4095
            dac_step = 1
            for j in range(0*dac_range,dac_range,dac_step):
                vals.append(j)
                dvals.append(j)
                # get high byte
                highbyte = j >> 8
                 # get low byte
                lowbyte = j & 0xFF
                if ismall < 4094:
                    smallbuf.extend([highbyte, lowbyte])
                    ismall+=2
                largebuf.extend([highbyte, lowbyte])
                ilarge += 2
            for j in range(0*dac_range,dac_range,dac_step):
                dvals.append(j)
            while True:
                print("Setup DAC with use ldac %d" % DAC.use_LDAC)
                #pdb.set_trace()
                if block_output2:
                #    DAC.xfer2(smallbuf)
                #    time.sleep(0.1)
                    while True:
                        DAC.xfer3(largebuf)
                    sys.exit(0)
                if send_vals:
                    for j in vals:
                        DAC.output_data(j)
                if send_dvals:
                    for j in dvals:
                        DAC.output_data(j)
                if ramp_up:
                    for i in range(0,dac_range,dac_step):
                       print("\tSetting value %d on DA3 with ldac %d" % (i, DAC.use_LDAC))
                       #DAC.output_data(0)
                       #time.sleep(0.001)
                       DAC.output_data(i)
                #       time.sleep(0.1)
                       #pdb.set_trace()
        #               DAC.output_data(0)
                if ramp_down:
                    for i in range(dac_range,0,-1* dac_step):
                         print("\tSetting value %d on DA3 with ldac %d" % (i, DAC.use_LDAC))
                         #DAC.output_data(0)
                         #time.sleep(0.001)
                         DAC.output_data(i)
                #         time.sleep(0.1)
                         #DAC.output_data(0)
                if not loop: sys.exit(1)
            DAC.close()
