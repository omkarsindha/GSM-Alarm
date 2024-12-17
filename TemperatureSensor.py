import os
import glob
import time
import traceback
from systemd import journal


SENSOR_DIR = '/sys/bus/w1/devices/'

class TemperatureSensor:
    """A class to read 1-wire (w1) sensor data DS18B20 from sysfs.

    Reads 1-wire data from the w1-gpio/w1-therm kernel drivers.
    https://www.kernel.org/doc/Documentation/w1/w1.generic
    https://www.kernel.org/doc/Documentation/w1/slaves/w1_therm

    These drives create files in sysfs under:
        /sys/bus/w1/devices
    Each device will appear as X number of files:

    Support is provided through the sysfs 'w1_slave file'.
    This module will not work if w1-gpio and w1-therm are not loaded beforehand
    """
    def __init__(self, debug=True):
        self.sensor_serials = self.discover_sensors()
        self.warning = False       # Error flag when reading sensors 
        self.debug = debug
        
    def discover_sensors(self):
        """
        Finds all folders starting with the DS18B20 family code (0x28).
        The format is <family>-<sensor_serial_number> e.g. <xx>-<xxxxxxxxxxxx>
        
        Returns: List of sensor serials extracted from the folder name
        """
        serials = []
        sensor_folders = glob.glob(SENSOR_DIR + '28-*')   # Gives a list of temp sensor folders
        for folder in sensor_folders:                 
            _, _, serial = folder.partition('28-')
            serials.append(serial)
        return serials
        
    def read_temp(self, serial: str) -> float:
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
        file = f'{SENSOR_DIR}28-'+serial+'/w1_slave'  # Converting the serial to the actual path
        try:
            with open(file, "r") as f:
                lines = f.readlines()
                if len(lines) != 2:
                    raise ValueError(f"Not two lines in {file}")
                # Parse temperature from lines[1]
                temp_data = lines[1].split("t=")
                if len(temp_data) == 2:
                    temp_c = int(temp_data[1]) / 1000.0
                    return round(temp_c,1)
                else:
                    raise ValueError("Invalid temperature data format.")
        except FileNotFoundError:
            raise ValueError(f"Sensor file not found: {file}")
        except Exception as e:
            raise ValueError(f"Error reading sensor {serial}: {e}")

                         
    def log(self, message: str) -> None:
        """
        Logs a message if debug mode is enabled.
        
        :param message: Message to log
        """
        if self.debug:
            journal.send(message)
            
    def get_readings(self) -> dict:
        """Returns a dictionary of sensor serial and their readings.

        Example: [{"xxxxxxxxx":25.23,...}]
        If there is a read error, will change warning to True.
        """
        readings = {}
        for serial in self.sensor_serials:
            try:
                temp_c = self.read_temp(serial)
            except (OSError, ValueError) as err:
                # SysFS w1_slave invalid format or failed CRC.
                error = str(err) if str(err) else str(err.__class__.__name__)
                message = f"Error reading sensor with serial '{serial}': {error}"
                self.warning = True
                self.log(message)
                self.log(traceback.format_exc())
            else:
                readings[serial] = temp_c
        return readings


if __name__ == '__main__':
    # When run directly do a simple self-test showing temperature readings.
    sensor = TemperatureSensor()
    for _ in range(10):
        print(sensor.get_readings())
        time.sleep(2)
