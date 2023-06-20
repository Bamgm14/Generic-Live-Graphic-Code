from instrument import * 
from typing import Union

class Keithley6487(Instrument):
    def __init__(self, port, baudrate=9600, timeout=2, parity = PARITY_NONE, stopbits=STOPBITS_TWO):
        super().__init__(port, baudrate, timeout, parity, stopbits, b'\n\r')
    @property
    def set_voltage(self):
        return self.VSET()
    
    @set_voltage.setter
    def set_voltage(self, value):
        self.VSET(value)
    
    @property
    def current_limit(self):
        return self.ILIM()
    @current_limit.setter
    def current_limit(self, value):
        self.ILIM(value)
    
    def VSET(self, value = None):
        query = "SOUR:VOLT"
        if value:
            self.write(f"{query} {value}".encode('ascii'))
            return None
        else:
            query = f"{query}?"
            self.write(query.encode('ascii'))
            return float(self.read_until())
        
    def voltage_range(self, value: Union[float, int] = None):
        if value:
            self.write(f"SOUR:VOLT:RANG {value}".encode('ascii'))
        else:
            self.write(b"SOUR:VOLT:RANG?")
            return float(self.read_until())
    def ILIM(self, value:float):
        if value:
            self.write(f"SOUR:VOLT:ILIM {value:.2e}".encode('ascii'))
        else:
            self.write(b"SOUR:VOLT:ILIM?")
            return float(self.read_until())
    def source(self, value:bool):
        value = "ON" if value else "OFF"
        self.write(f"SOUR:VOLT:STAT {value}".encode('ascii'))
    def enable_source(self):
        self.source(True)
    def disable_source(self):
        self.source(False)
    def IDN(self):
        self.write(b"*IDN?")
        return str(self.read_until(), 'utf-8')
    
        