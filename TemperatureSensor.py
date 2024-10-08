import os
import glob
import time
from utils.file_utils import add_new_sensor
import traceback


class TemperatureSensor:
    def __init__(self, base_dir='/sys/bus/w1/devices/'):
        os.system('sudo modprobe w1-gpio')
        os.system('sudo modprobe w1-therm')
        self.sensor_files = []
        device_folders = glob.glob(base_dir + '28*')   # Gives a list of temp sensor folders
        for folder in device_folders:                  # Get path to the slave file 
            self.sensor_files.append(folder + '/w1_slave')
        
        add_new_sensor(self.sensor_files)        # Update the sensor config according to the detected sensors

    def read_temp_raw(self, file):
        """
        Reads the temperature sensor file and returns the lines as list
        """
        with open(file, 'r') as f:
            lines = f.readlines()
        return lines

    def read_temp(self):
        """
        Returns a list of dict of sensor and their readings
        Example: [{sys/bus/...:"25.23"},...]  
        """
        readings = []
        for file in self.sensor_files:
            lines = self.read_temp_raw(file)
            try:
                while lines[0].strip()[-3:] != 'YES':
                    time.sleep(0.2)
                    lines = self.read_temp_raw()
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:              # Append reading only if temperature is available
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    readings.append({file : round(temp_c, 2)})
            except Exception as err:
                error = str(err) if str(err) else str(err.__class__.__name__)
                print("Error while reading temperature: %s" % error)
                print(traceback.format_exc())
        return readings
        
if __name__ == '__main__':
    sensor = TemperatureSensor()
    for _ in range(10):
        print(sensor.read_temp())
        time.sleep(2)