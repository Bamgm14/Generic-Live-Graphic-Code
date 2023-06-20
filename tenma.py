from instrument import *
import asyncio
class TENMAException(Exception):
    pass

class TENMA_72_7210(Instrument):
    def __init__(self, port, baudrate=9600, timeout=2, parity=PARITY_NONE, stopbits=STOPBITS_ONE):
        super().__init__(port, baudrate, timeout, parity, stopbits, b'\n')
        self.channel = 1
    def channel_default(self, channel):
        self.channel = channel
    
    @property
    def set_voltage(self):
        return float(self.VSET(self.channel))
    
    @property
    def set_current(self):
        return float(self.ISET(self.channel))
    
    @set_voltage.setter
    def set_voltage(self, voltage):
        self.VSET(self.channel, voltage)
    
    @set_current.setter
    def set_current(self, voltage):
        self.ISET(self.channel, voltage)
    
    @property
    def voltage(self):
        return float(self.VOUT(self.channel))
    @property
    def current(self):
        return float(self.IOUT(self.channel))
    
    
    def VSET(self, channel = 1, voltage = None):
        query = f'VSET{channel}'
        if voltage:
            query = f'{query}:{voltage}'
        else:
            query = f'{query}?'
        self.write(bytes(query,'ascii'))
        return self.read_until()

    def ISET(self, channel = 1, current = None):
        query = f'ISET{channel}'
        if current:
            query = f'{query}:{current}'
        else:
            query = f'{query}?'
        self.write(bytes(query,'ascii'))
        return self.read_until()
    
    def VOUT(self, channel = 1):
        query = f'VOUT{channel}?'
        self.write(bytes(query,'ascii'))
        return self.read_until()
    
    def IOUT(self, channel = 1):
        query = f'IOUT{channel}?'
        self.write(bytes(query,'ascii'))
        return self.read_until()
    def OCP(self, on_off = True):
        query = f"OCP{int(on_off)}"
        self.write(bytes(query,'ascii'))
        return self.read_until()

    