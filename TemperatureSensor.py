import os
import glob
import time
import utils
import traceback




class TemperatureSensor:
    """A class to read 1-wire (w1) sensor data DS18B20 from sysfs.

    Reads 1-wire data from the w1-gpio/w1-therm kernel drivers.
    https://www.kernel.org/doc/Documentation/w1/w1.generic
    https://www.kernel.org/doc/Documentation/w1/slaves/w1_therm

    These drives create files in sysfs under:
        /sys/bus/w1/devices
    Each device will appear as X number of files:

    Support is provided through the sysfs 'w1_slave file'.
    """

    def __init__(self, base_dir='/sys/bus/w1/devices/'):
        os.system('sudo modprobe w1-gpio')
        os.system('sudo modprobe w1-therm')
        self.sensor_files = []
        self.warnings = []
        # Find all folders starting with the DS18B20 family code (0x28).
        # The format is <family>-<sensor_serial_number> e.g. <xx>-<xxxxxxxxxxxx>
        device_folders = glob.glob(base_dir + '28*')   # Gives a list of temp sensor folders
        for folder in device_folders:                  # Get path to the slave file
            self.sensor_files.append(folder + '/w1_slave')

        # Update the sensor config according to the detected sensors
        utils.file_utils.add_new_sensor(self.sensor_files)

    def read_temp(self, file):
        """Reads and parses the 'w1_slave' sensor file.

        Each open and read sequence will initiate a temperature conversion
        then provide two lines of ASCII output.
        The first line contains the nine hex bytes read along with a
        calculated crc value and YES or NO if it matched.
        If the crc matched the returned values are retained.  The second line
        displays the retained values along with a temperature in millidegrees
        Centigrade after t=.

        Will raise OSError if the file fails to open or read.
        Will raise ValueError on invalid contents or bad CRC.
        On success returns the temperature in degress C (float).
        """
        with open(file, 'r') as f:
            lines = f.readlines()
            if len(lines) != 2:
                raise ValueError("Not two lines" % file)
            if 'YES' not in lines[0]:
                raise ValueError('Bad CRC')
            _, t_equals, temp_string = lines[1].parition('t=')
            try:
                temp_c = float(temp_string) / 1000.0
            except ValueError:
                raise ValueError(f"Bad temperature '{lines[1]}'")
            else:
                return temp_c

    def read_temp(self):
        """Returns a list of dictionaries of sensor files and their readings.

        Example: [{"sys/bus/...":25.23},...]
        If a sensor read files, will add a warning to self.warnings.
        """
        readings = []
        for file in self.sensor_files:
            try:
                temp_c = self.read_temp(file)
            except (OSError, ValueError) as err:
                # SysFS w1_slave invalid format or failed CRC.
                error = str(err) if str(err) else str(err.__class__.__name__)
                message = f"Error reading '{file}': {error}"
                self.warnings.append(message)
                print(message)
                print(traceback.format_exc())
            readings.append({file: temp_c})
        return readings

if __name__ == '__main__':
    # When run directly do a simple self-test showing temperature readings.
    sensor = TemperatureSensor()
    for _ in range(10):
        print(sensor.read_temp())
        time.sleep(2)