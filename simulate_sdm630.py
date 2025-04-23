#!/usr/bin/env python
                
# Simulate SDM630 for testing export limitation on Growatt MIC 600TL-X
# Sources:
# https://github.com/EmbedME/growatt_simulate_sdm630/blob/main/growatt_simulate_sdm630.py
# https://github.com/hankipanky/esphome-fake-eastron-SDM630/blob/master/fake-eastron.yaml

import sys
import serial
import binascii
import struct


class SimulateSdm630:
    def __init__(self, serialPort):
        # open serial port of RS485 interface
        self.serial_port = serial.Serial(port=serialPort, baudrate=9600)
        # set up a dictionary for all possibly queried registers
        self.register_values = {
            0: 0,   # register 0: phase A voltage
            2: 0,   # register 2: phase B voltage
            4: 0,   # register 4: phase C voltage
            6: 0,   # register 6: phase A current
            8: 0,   # register 8: phase B current
            10: 0,  # register 10: phase C current
            12: 0,  # register 12: phase A power
            14: 0,  # register 14: phase B power
            16: 0,  # register 16: phase C power
            18: 0,  # register 18: phase A apparent power
            20: 0,  # register 20: phase B apparent power
            22: 0,  # register 22: phase C apparent power
            24: 0,  # register 24: phase A reactive power
            26: 0,  # register 26: phase B reactive power
            28: 0,  # register 28: phase C reactive power
            30: 0,  # register 30: phase A power factor
            32: 0,  # register 32: phase B power factor
            34: 0,  # register 34: phase C power factor
            48: 0,  # register 48: Sum of line currents
            52: 0,  # register 52: Total system power
            56: 0,  # register 56: Total system volt amps
            70: 0,  # register 70: Frequency of supply voltages
            200: 0,  # register 200: Not supported
            342: 0   # register 342: Total kWh
        }

    def set_register_value(self, register, value):
        if register in self.register_values:
            self.register_values[register] = value
        else:
            print("Register not available.")

    def get_register_value(self, register):
        return self.register_values.get(register, None)

    def format_packet(self, packet):
        hex_string = binascii.hexlify(bytes(packet))
        pair_string = ' '.join([hex_string[i:i+2].decode('utf-8') for i in range(0, len(hex_string), 2)])
        return pair_string

    def send_response(self, functioncode, wordsize, value):
        # construct response
        wordsize = 2
        response = [0x02, functioncode, wordsize * 2] # our address is expected to be two, we respond to the received function code with 4 bytes (1 word = 2 bytes)
        response.extend(struct.pack('>f', value)) # we write the number from 'value' into the response buffer
        crc = self.calc_crc(response)
        response.append(int(crc & 0xff)) # we append..
        response.append(int((crc >> 8) & 0xff)) # ..a crc to our reponse
        #print("response", self.format_packet(response), "(Value: " + str(value) + ")")
        self.serial_port.write(response)

    def receive_request(self):
        recbuffer = [0] * 8 # initialize receive buffer
        while True:
            # read in one byte and add it to the receive buffer, trim buffer to 8 bytes
            data = self.serial_port.read(1) # we read bytewise to ensure a complete packet. read(8) might start and end anywhere.
            recbuffer = recbuffer + list(data)
            recbuffer = recbuffer[-8:]

            if self.calc_crc(recbuffer) != 0:
                continue

            # extract parameters from packet
            serverAddr = recbuffer[0] # requested server address (the SDM630 is expected to be at address 2)
            functioncode = recbuffer[1]
            register = recbuffer[2] << 8 | recbuffer[3]
            wordsize = recbuffer[4] << 8 | recbuffer[5] # the amount of requested words (aka 16-bit values)

            #print("Got request ", self.format_packet(recbuffer))
            #print("\tRegister " + str(register))

            return serverAddr, functioncode, register, wordsize

    def listen(self):
        try:
            while True:
                serverAddr, functioncode, register, wordsize = self.receive_request()

                if serverAddr != 2:
                    continue 

                if register in self.register_values:
                    value = self.register_values[register]
                    #if register == 52:
                    #    print("Demanding " + str(value) + " Watts...")
                    self.send_response(functioncode, wordsize, value)

        finally:
            self.serial_port.close()

    def calc_crc(self, data):
        crc = 0xFFFF
        for pos in data:
            crc ^= pos 
            for i in range(8):
                if ((crc & 1) != 0):
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc
