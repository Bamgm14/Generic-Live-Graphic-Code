#Created By Arpan George Mathew (Bamgm14)
from serial import *
class InstrumentException(Exception):
    pass

class Instrument:
    def __init__(self, port, baudrate=9600, timeout=2, parity = PARITY_NONE, stopbits=STOPBITS_ONE, terminate = b'\r\n'):
        self.port = port
        self.terminate = terminate
        self.ser = Serial(port, baudrate, parity=parity, timeout=timeout, stopbits=stopbits)
        
    def close(self):
        self.ser.close()
    def write(self, command):
        self.ser.write(command + self.terminate)
    def read(self, bytes):
        return self.ser.read(bytes)
    def read_until(self):
        return self.ser.read_until(self.terminate)