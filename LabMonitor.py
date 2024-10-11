from Config.Config import Config
from TemperatureSensor import TemperatureSensor
from SIM7600x import SIM7600x
from UPS import UPS
import time
import os
import json 
import threading
import schedule
import traceback
from utils import file_utils
from utils import utils
import gsmmodem

class LabMonitor(threading.Thread):
    """
    A class to monitor laboratory conditions including temperature and power status.
    Runs as a separate thread.
    """
    def __init__(self, check_interval:int=2, debug:bool=False, **kwargs):
        super(LabMonitor, self).__init__(name="Monitor", **kwargs)
        
        # Initialize configuration and components
        self.sensor = TemperatureSensor()
        file_utils.add_new_sensor(self.sensor.sensor_serials) # Add new sensor to config file
        
        self.config = Config()
                
        self.ups = UPS()
        self.sms_thread = SIM7600x(parent=self, debug=debug)
        self.sms_thread.start()
        
        self.debug: bool = debug
        self.check_interval: int = check_interval
        self.last_msg_time = time.time() - self.config.alert_interval
        self.end_event = threading.Event()
        
        
        self.alert_sent: bool = False
        self.power_source: str = "120V-AC"    # Initial power source is 120V-AC
        self.low_battery = False
        self.readings: dict = {}
        self.sensors_above_threshold: dict = {} # Dict of sensors serial as key and their temp as value (that are above threshold)

        self.schedule_daily_status()
        self.log("Initiated an instance of monitor thread")
         
    def run(self):
        """
        Main method that runs when the thread starts.
        Calls monitor_loop.
        """
        try:
            self.monitor_loop()
        except Exception as err:
            error = str(err) if str(err) else str(err.__class__.__name__)
            self.log("Thread failed: %s" % error)
            self.log(traceback.format_exc())
            
    def monitor_loop(self):
        """Main logic for Lab Monitor"""
        while not self.end_event.is_set():
            # Read current temperature and power status
            self.readings = self.sensor.get_readings()  # Dict of sensor serial and its temp {"xxx":xx, ...}
            power = self.ups.get_power_source()  # 120V-AC or UPS or None if error

            self.log(f"Status (Temperature Readings: {self.readings} || Power: {power})")

            if self.config.armed:  # If the Alarm is active
                cur_time = time.time()
                
                # Process each sensors reading to check if the temperature is above the trigger threshold
                for sensor_serial in self.readings:    # Looping through the keys i.e sensor serial
                    temperature = self.readings[sensor_serial]
                    if sensor_serial in self.config.sensors:
                        trigger = self.config.sensors[sensor_serial]['trigger']
                        if temperature > trigger:
                            self.sensors_above_threshold[sensor_serial] = {
                                "temperature": temperature,
                                "name": self.config.sensors[sensor_serial]['name']
                            }  

                # Check if temperature has returned to normal
                for sensor_serial in self.readings:     # Looping through the keys i.e sensor serial
                    temperature = self.readings[sensor_serial]
                    if sensor_serial in self.sensors_above_threshold:
                        trigger = self.config.sensors[sensor_serial]['trigger']
                        if temperature < trigger - self.config.hysteresis:
                            self.log(f"{self.sensors_above_threshold[sensor_serial].get('name')} is back to normal temperature")
                            del self.sensors_above_threshold[sensor_serial]                     # Delete it from the list
                            
                            if not self.sensors_above_threshold:     # Only if sensor list gets empty send back to normal message    
                                self.log("Sending temperature back to normal message")       
                                self.alert_sent = False
                                msg = f"Alert Resolved\n\nTemperature is back to normal :)\n\nLocation: {self.config.location} \nTime: {utils.get_rdbl_time()}"
                                self.sms_thread.enqueue_sms(self.config.numbers, msg)
                                file_utils.write_history("Temperature back to normal")

                # Send alert if temperature is still high after alert interval
                cur_time = time.time()
                if cur_time - self.last_msg_time > self.config.alert_interval and self.sensors_above_threshold:
                    if self.config.repeat_alerts or not self.alert_sent: # Check if repeat alerts is on or alert is already sent
                        self.log("Sending High Temperature Message")
                        self.last_msg_time = time.time()
                        self.alert_sent = True

                        # Build the message with sensor names and their temperatures
                        sensor_details = "\n".join(
                            [f"{info['name']}: {info['temperature']}°C" for info in self.sensors_above_threshold.values()]
                        )
                        msg = f"Alert\n\nHigh temperature\n\nSensors Above threshold\n{sensor_details}\n\nLocation: {self.config.location}\nTime: {utils.get_rdbl_time()}"
                        self.sms_thread.enqueue_sms(self.config.numbers, msg)
                        file_utils.write_history("High temperature")
                    
                # Handle changes in power source
                if power:     # Checking for None
                    if power != self.power_source:
                        self.power_source = power
                        self.log("Sending power type changed message")
                        if self.power_source == "120V-AC":
                            msg = f"Alert\n\nPower lost, running on battery power\n\nLocation: {self.config.location}\nTime: {utils.get_rdbl_time()}"
                        else:
                            msg = f"Alert Resolved\n\nPower has been recovered :)\n\nLocation: {self.config.location}\nTime: {utils.get_rdbl_time()}"
                        self.low_battery = False           # As, if UPS to GRID then Not low battery, else if GRID to UPS then we want to send low battery msg 
                        self.sms_thread.enqueue_sms(self.config.numbers, msg)
                        file_utils.write_history(f"Power changed to {power}")
                        
                # Case when battery is low 
                if power == "UPS":
                    percentage = self.ups.get_battery_level()
                    if percentage:     # Checking for None
                        if percentage <= 20 and self.low_battery == False:
                            self.log("Sending low battery message")
                            msg = f"Alert\n\nBattery is less than 20%\n\nLocation: {self.config.location}\nTime: {utils.get_rdbl_time()}"
                            self.sms_thread.enqueue_sms(self.config.numbers, msg)
                            file_utils.write_history("Low battery")
                            self.low_battery = True
                    
                # Run any scheduled daily status reports
                schedule.run_pending()
            time.sleep(self.check_interval)
            
    def stop(self, block=False):
        """
        Signal the thread to end. Block only if block=True.
        """
        self.end_event.set()
        self.sms_thread.stop()
        if block:
            self.join()
            
    def get_config(self) -> dict:  
        """
        Get all the information from Config, SIM7600x and Monitor in form of a dictionary
        """
        network_type = self.sms_thread.network_type
        signal_strength = self.sms_thread.signal_strength
        battery = self.ups.get_battery_level()
        battery = 0 if not battery else battery
        # Config might have old sensors so filtering it to get only the ones available in the latest readings
        sensor_serials = list(self.readings.keys())                               
        filtered_sensors = {sensor_serial: info for sensor_serial, info in self.config.sensors.items() if sensor_serial in sensor_serials}

        # Initialize the intersection list
        intersection = []
        for sensor_serial in self.readings:
            temperature = self.readings[sensor_serial]
            if sensor_serial in filtered_sensors:
                sensor_info = filtered_sensors[sensor_serial]
                combined_info = {
                    "name": sensor_info["name"],
                    "sensor": sensor_serial,
                    "trigger": sensor_info["trigger"],
                    "temperature": temperature
                }
                intersection.append(combined_info)
            
        return {
                "high_temperature": bool(self.sensors_above_threshold), 
                "location": self.config.location,
                "hys": self.config.hysteresis, 
                "interval": self.config.alert_interval / 60, 
                "daily_report_time": self.config.daily_report_time,
                "armed": self.config.armed,
                "send_daily_report": self.config.send_daily_report,
                "repeat_alerts": self.config.repeat_alerts,
                "signal_strength": signal_strength, 
                "signal_type": network_type, 
                "pi_time": utils.get_rdbl_time(),  
                "numbers": self.config.numbers_list,
                "power": self.power_source,
                "battery": self.ups.get_battery_level(),
                "sensors": intersection
                }
    
    def schedule_daily_status(self):
        """
        Schedules the daily report SMS
        """
        self.config = Config()
        schedule.clear('daily_status')
        self.log(f"Scheduled daily status for {self.config.daily_report_time}")
        schedule.every().day.at(self.config.daily_report_time).do(self.send_daily_status).tag('daily_status')

    def send_daily_status(self):
        """
        Sends daily report SMS to numbers who want daily report
        """
        if self.config.send_daily_report:
            self.log("Sent daily status message")
            msg = f"Daily Report\n\nLocation: {self.config.location}\nTime: {utils.get_rdbl_time()}"
            self.sms_thread.enqueue_sms(self.config.daily_numbers, msg)
            file_utils.write_history("Daily report")
            
    def log(self, message):
        """
        Logs a message if debug mode is enabled
        """
        if self.debug:
            print(message)
            
    def handle_sms(self, sms: gsmmodem.modem.ReceivedSms):
        """
        Replies to SMS by the users of the Monitor after Authenticating and Authorizing
        """
        text = sms.text.lower().strip()
        num = sms.number
        print(type(sms))
        if num in self.config.numbers:  # Check if the message came from the list of numbers in the database
            name = ''
            for contact in self.config.numbers_list:        # Getting the name corresponding to the number
                 if contact['number'] == num:
                    name = contact['name']
        
            if text == 'status':  # Same for admin and normal users
                config = self.get_config()
                armed = 'Armed' if config['armed'] else 'Disarmed'
                repeat_alerts = f"Alert Interval: {int(config['interval'])} minutes" if config['repeat_alerts'] else f"Repeat Alerts: {config['repeat_alerts']}"
                message = f"Arm/Disarm: {armed}\nPower: {config['power']}\n{repeat_alerts}"
                self.sms_thread.enqueue_sms([num], message)
                file_utils.write_history(f"Status request by {name}")
                return

            if text == 'time':  # Same for admin and normal users
                message = f"Time: {utils.get_rdbl_time()}"
                self.sms_thread.enqueue_sms([num], message)
                file_utils.write_history(f"Time request by {name}")
                return

            if text == 'help':
                admin_help = "1. status\n2. time\n3. set repeat-alerts [on/off]\n4. set alert-interval [value in minutes]"
                normal_help = "1. status\n2. time"
                help_message = admin_help if num in self.config.admins else normal_help   # Seperate for both
                self.sms_thread.enqueue_sms([num], help_message)
                file_utils.write_history(f"Help request by {name}")
                return

            if num in self.config.admins:  # Additional commands for admin users
                parts = text.split()
                if len(parts) == 3:
                    if parts[0] == 'set' and parts[1] == 'repeat-alerts' and parts[2] in ['on', 'off']:
                        status = parts[2].lower()
                        if status == 'on':
                            file_utils.update_config(repeat_alerts = True)  
                        else:
                            file_utils.update_config(repeat_alerts = False)  
                        self.sms_thread.enqueue_sms([num], f"Repeat-Alerts set to '{status}'.")
                        file_utils.write_history(f"Repeat-Alerts set to '{status}' by {name}")
                        
                    elif parts[0] == 'set' and parts[1] == 'alert-interval' and utils.is_positive_number(parts[2]):
                        interval = int(parts[2])
                        file_utils.update_config(interval = interval) 
                        self.sms_thread.enqueue_sms([num], f"Alert interval set to {interval} minutes")
                        file_utils.write_history(f"Alert interval set to {interval} minutes by {name}")                       
                        
                    else:
                        self.sms_thread.enqueue_sms([num], "Invalid value for repeat-alerts. Please enter 'on' or 'off'.")
                        file_utils.write_history(f"Invalid command sent by {name}")
                    return 

            self.sms_thread.enqueue_sms([num], "Invalid command. Send 'help' for more details.")
            file_utils.write_history(f"Invalid command sent by {name}")

            
           
        
if __name__ == "__main__":
    # Create and start a LabMonitor instance for testing
    monitor = LabMonitor(debug=True)
    monitor.start()
    time.sleep(60)  
    monitor.stop()