#!/usr/bin/env python
"""
Stripped down Digilent PMOD DA3 demonstration using the SPI device on Raspberry Pi

Two options : explicitly using the LDAC output/not.

Adam Stephen.
"""

"""-----------------------------------------------------------"""

# import necessary modules
# SPI communication
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

    def close(self):
        self.dac.close()


from itertools import chain

if __name__ == '__main__':
#    pdb.set_trace()
    ldacs = [DA3(use_LDAC = False), DA3(use_LDAC = True)]
    ldacs = [DA3(use_LDAC = False)]
    ldacs = [ DA3(use_LDAC = False)]
    while True:
        for DAC in ldacs:
            DAC.setup()
            vals = []
            dvals = []
            #for j in chain(range(0,dac_range,dac_step), range(0,dac_range, ), range(dac_range, 0, -1*dac_step)):
            #for j in range(0,int(0.5*dac_range),dac_step):
            for j in range(0*dac_range,dac_range,dac_step):
                vals.append(j)
                dvals.append(j)
            for j in range(0*dac_range,dac_range,dac_step):
                dvals.append(j)
            while True:
                print("Setup DAC with use ldac %d" % DAC.use_LDAC)
                for j in vals:
                    DAC.output_data(j)
                for j in dvals:
                    DAC.output_data(j)
                for i in range(0,dac_range,dac_step):
                   print("\tSetting value %d on DA3 with ldac %d" % (i, DAC.use_LDAC))
                   #DAC.output_data(0)
                   #time.sleep(0.001)
                   DAC.output_data(i)
                   #time.sleep(0.0i01)
    #               DAC.output_data(0)
                for i in range(dac_range,0,-1* dac_step):
                     print("\tSetting value %d on DA3 with ldac %d" % (i, DAC.use_LDAC))
                     #DAC.output_data(0)
                     #time.sleep(0.001)
                     DAC.output_data(i)
                     #time.sleep(0.1)
    #                 DAC.output_data(0)
                time.sleep(0.1)
                sys.exit(1)
            DAC.close()
