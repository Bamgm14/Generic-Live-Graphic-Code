from threading import Thread, Event
import pandas as pd
import time
from sr510 import SR510
from tenma import TENMA_72_7210
from Keithley6487 import Keithley6487
from pymeasure.instruments.keithley import Keithley2450, Keithley2400
from typing import Union
from datetime import datetime
class Experiment:
    def __init__(self,lockin: SR510, laser_power: Union[TENMA_72_7210, Keithley6487, Keithley2450], source_drain: Union[TENMA_72_7210, Keithley6487, Keithley2450], gate: Union[TENMA_72_7210, Keithley6487, Keithley2450], wavelength: float):
        self.lockin = lockin
        self.source_drain = source_drain
        self.laser_power = laser_power
        self.gate = gate
        self.wavelength = wavelength
        self.data = []
        self.thread = None
        self.start_time = None
        self.flag = False
        self.stop_time = None
        #print(self.thread)
    def start(self):
        self.data = []
        if self.thread:
            raise Exception("Experiment already running")
        self.flag = True
        self.thread = Thread(target=self.run)
        self.thread.start()
        
    def run(self):
        self.freq = self.lockin.frequency
        #self.pre_time_constant = self.lockin.pre_time_constant
        #self.post_time_constant = self.lockin.post_time_constant
        self.phase = self.lockin.phase
        self.sensitivity = self.lockin.sensitivity
        self.start_time = time.time()
        while self.flag:
            output = self.lockin.output
            source_voltage = self.source_drain.set_voltage
            gate_voltage = None #self.gate.voltage
            self.data.append((time.time() - self.start_time, source_voltage, output, gate_voltage))
            
    def stop(self):
        self.flag = False
        self.thread.join()
        del self.thread
        self.thread = None
        self.filename = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H.%M.%S") + ".csv"
        self.stop_time = time.time()
        print(self.stop_time - self.start_time)
    def write(self, path = ''):
        with open(path + "/" + self.filename, 'w') as f:
            f.write("#Experiment started at: " + datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H.%M.%S") + "\n")
            f.write("#Experiment stopped at: " + datetime.fromtimestamp(self.stop_time).strftime("%Y-%m-%d %H.%M.%S") + "\n")
            f.write("#Frequency: " + str(self.freq) + "\n")
            f.write("#Wavelength: " + str(self.wavelength) + "\n")
            f.write("#Phase: " + str(self.phase) + "\n")
            #f.write("Pre time constant: " + str(self.pre_time_constant) + "\n")
            #f.write("Post time constant: " + str(self.post_time_constant) + "\n")
            f.write("#Sensitivity: " + str(self.sensitivity) + "\n")
            f.write("time,source-voltage,output,gate-voltage\n")
            for x in self.data:
                f.write(f"{x[0]},{x[1]},{x[2]},{x[3]}\n")
        return path + "/" + self.filename
    
    def get_data(self):
        return self.data
    def collected_to_df(self):
        self.df = pd.DataFrame({
            'time': [x[0] for x in self.data], 
            'source-voltage': [x[1] for x in self.data], 
            'output': [x[2] for x in self.data], 
            'gate-voltage': [x[3] for x in self.data]
        })
        return self.df
        
        #super().__del__()
    def __str__(self):
        #{self.sr510.port or 'DEBUG'}, {self.tenma.port or 'DEBUG'}
        return f"Experiment({self.filename}, )\nStatus: {'Running' if self.thread else 'Stopped'}\nData points: {len(self.data)} "
if __name__ == "__main__":
    experiment = Experiment('test.csv', 'COM12', 'COM9',1.5*10**-2)
    print(experiment)
    experiment.start()
    print()
    time.sleep(1)
    print(experiment)
    experiment.stop()
    try:
        for x in range(1, len(experiment.get_data())):
            print(experiment.get_data()[x][0] - experiment.get_data()[x-1][0])
    except Exception as e:
        pass
    print(experiment)
    experiment.write()
    print(experiment)