from instrument import *
import numpy as np
import time

class SR510(Instrument):
    def __init__(self, port, baudrate=9600, timeout=2, parity = PARITY_NONE, stopbits=STOPBITS_TWO):
        super().__init__(port, baudrate, timeout, parity, stopbits, b'\r')

    @property
    def frequency(self):
        return float(self.F())
    
    @property
    def sensitivity(self):
        return self.G()
    @sensitivity.setter
    def sensitivity(self, value):
        self.G(value)
    
    @property
    def output(self):
        return float(self.Q())
    
    @property
    def phase(self):
        return float(self.P())
    @phase.setter
    def phase(self, phase):
        print(phase)
        self.P(phase)
        
    @property
    def pre_time_constant(self):
        return float(self.T("pre"))
    @pre_time_constant.setter
    def pre_time_constant(self, value):
        self.T("pre", value)
    
    @property
    def post_time_constant(self):
        return float(self.T("post"))
    @post_time_constant.setter
    def post_time_constant(self, value):
        self.T("post", value)
        
        
    def autophase(self, avgstep = 3):
        #WILL BE SLOW
        value = 0
        best = 0
        for phase in np.arange(-180, 181, 10):
            self.phase = phase
            lst = []
            for _ in range(avgstep):
                lst.append(self.output)
            if (var := abs(np.mean(lst))) > value:
                value = var
                best = phase
        for phase in np.arange(best - 10, best + 10, 1):
            self.phase = phase
            lst = []
            for _ in range(avgstep):
                lst.append(self.output)
            if (var := abs(np.mean(lst))) > value:
                value = var
                best = phase
        for phase in np.arange(best - 1, best + 1, 0.1):
            self.phase = phase
            lst = []
            for _ in range(avgstep):
                lst.append(self.output)
            if (var := abs(np.mean(lst))) > value:
                value = var
                best = phase
        self.phase = best
        return best
        
    def fast_autophase(self, avgstep = 3):
        def descent(x, a, b):
            return x + (a*np.cos(x) - b*np.sin(x))/(a*np.sin(x) + b*np.cos(x)) #??????????????????????? [HOW DID THIS WORK?????]
        self.phase = 0
        lst = []
        for x in range(avgstep):
            lst.append(self.output)
        zero = np.mean(lst)
        self.phase = 180
        lst = []
        for x in range(avgstep):
            lst.append(self.output)
        pi = np.mean(lst)
        c = (zero + pi)/2
        b = zero - c
        self.phase = 90
        lst = []
        for x in range(avgstep):
            lst.append(self.output)
        a = np.mean(lst) - c
        #print(a, b, c)
        x_1 = 0
        x_2 = descent(x_1, a, b)
        while abs(x_1 - x_2) > 1.5 * (10 ** -4):
            x_1 = x_2
            x_2 = descent(x_1, a, b)
        x_2 = x_2 % (2*np.pi)
        self.phase = round(x_2*180/np.pi, 1)
        print(x_2, round(x_2*180/np.pi, 1))
        #print(x_1, x_2)
        return self.phase

    def F(self):
        self.ser.write(b'F\r')
        return self.read_until() 
    
    def A(self, mode = None):
        modes = {"auto": 1, "manual": 0}
        mode = modes.get(mode, None)
        if mode:
            self.write(bytes(f'A {mode}', 'ascii'))
        else:
            self.write(b'A')
        return self.ser.read_until(expected=self.terminate).decode('ascii')
    
    def B(self, mode = None):
        modes = {"set": 1, "taken": 0}
        mode = modes.get(mode, None)
        if mode:
            self.write(bytes(f'B {mode}','ascii'))
        else:
            self.write(b'B')
        return self.read_until()
         
    def C(self, mode = None):
        modes = {"phase": 1, "frequency": 0}
        mode = modes.get(mode, None)
        if mode:
            self.ser.write(bytes(f'C {mode}','ascii'))
        else:
            self.write(b'C')
        return self.read_until()
    
    def G(self, voltage = None):
        #print(voltage_mode, voltage_value)
        modes = {1e-8: 1, 2e-8:  2, 5e-8: 3,
                 1e-7: 4, 2e-7: 5, 5e-7: 6,
                 1e-6: 7, 2e-6: 8, 5e-6: 9, 
                 1e-5: 10, 2e-5: 11, 5e-5:12, 
                 1e-4: 13, 2e-4: 14, 5e-4: 15,
                 1e-3: 16, 2e-3: 17, 5e-3: 18,
                 1e-2: 19, 2e-2: 20, 5e-2: 21,
                 1e-1: 22, 2e-1: 23, 5e-1: 24,}
        mode = modes.get(voltage, None)
        #print(mode)
        if mode:
            self.write(bytes(f'G {mode}', 'ascii'))
            return None
        else:
            self.write(b'G')
            var = list(modes.keys())[list(modes.values()).index(int(self.read_until().decode('ascii')))]
            return var
    
    def M(self, mode = None):
        modes = {"2f": 1, "f": 0}
        mode = modes.get(mode, None)
        if mode:
            self.write(bytes(f'M {mode}','ascii'))
        else:
            self.write(b'M')
        return self.read_until()
    
    def R(self, mode = None):
        modes = {"positive": 0, "symmetric": 1, "negative": 2}
        mode = modes.get(mode, None)
        if mode:
            self.write(bytes(f'R {mode}','ascii'))
        else:
            self.write(b'R')
        return self.read_until()
    
    def Q(self):
        self.write(b'Q')
        return self.read_until()
    
    def T(self, mode = None, value = None):
        modes = {"pre": 1, "post": 0}
        pre_modes = {
            1e-3: 1, 3e-3: 2,
            1e-2: 3, 3e-2: 4,
            1e-1: 5, 3e-1: 6,
            1: 7, 3: 8,
            10: 9, 30: 10,
            100: 11
        }
        post_modes = {
            "None": 0,
            0.1: 1,
            1: 2,
        }
        mode = modes.get(mode, None)
        if mode == 1:
            value = pre_modes.get(value, None)
        elif mode == 0:
            value = post_modes.get(value, None)
        else:
            raise InstrumentException('Mode must be "pre" or "post"')
        self.write(bytes(f'T {mode} {value}','ascii'))
        return self.read_until()
    
        
    
    def P(self, angle = None):
        if isinstance(angle, type(None)):
            self.write(b'P')
        else:
            if 999 < angle or angle < -999:
                raise InstrumentException('Angle must be between -999 and 999')
            self.write(bytes(f'P {angle}','ascii'))
        return self.read_until()
    