#from pymodbus.client.sync import ModbusSerialClient # pymodbus 2.x.x
from pymodbus.client import ModbusSerialClient # pymodbus 3.x

import ctypes # To cast uint16_t as int16_t

class PollDeye:
    def __init__(self, port):
        self.client = ModbusSerialClient(method='rtu', port=port, baudrate=9600, timeout=1)
        connection = self.client.connect()
        if connection is None:
            print("Connection already established")
        elif not connection:
            print("Failed to connect to client")
            raise ConnectionError("Failed to connect to Modbus client")

    def get_register(self, register):
        #result = self.client.read_holding_registers(register, 1, unit=0x01) # pymodbus 2.x
        result = self.client.read_holding_registers(register, 1, slave=0x01) # pymodbus 3.x
        if not result.isError():
            return result.registers[0]
        else:
            print("Error reading register \"" + str(register) + "\"")
            return None

    def close(self):
        self.client.close()
