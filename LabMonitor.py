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
from utils.utils import get_rdbl_time, is_number
from utils.file_utils import write_history, update_config

class LabMonitor(threading.Thread):
    """
    A class to monitor laboratory conditions including temperature and power status.
    Runs as a separate thread.
    """
    def __init__(self, check_interval=5, debug=False, **kwargs):
        super(LabMonitor, self).__init__(name="Monitor", **kwargs)
        
        # Initialize configuration and components
        self.config = Config(config_path="Config/config.json")
        self.sensor = TemperatureSensor()
        self.ups = UPS()
        self.gsm_modem = SIM7600x(parent=self, debug=debug)
        self.gsm_modem.connect()
        
        self.debug = debug
        self.check_interval = check_interval
        self.last_msg_time = time.time() - self.config.alert_interval
        self.end_event = threading.Event()
        self.status: str = "GREEN"  # Initial status is GREEN (normal)
        self.power: str = "120V-AC"    # Initial power source is 120V-AC
        self.power_last_state: str = "120V-AC"
        self.low_battery = False
        self.temp = 0
        
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
            self.temp = self.sensor.read_temp()
            self.power = self.ups.get_status() # 120V-AC or UPS
            self.log(f"Status (Temperature: {self.temp}°C || Power: {self.power})") 
            
            if self.config.armed:       # If the Alarm is active
                cur_time = time.time()
                
                # Check if temperature exceeds maximum allowed
                if self.temp > self.config.max_temp:
                    self.status = "RED"

                # Check if temperature has returned to normal
                if self.temp < self.config.max_temp - self.config.hysteresis and self.status == "RED":
                    self.log("Sending temprerature back to normal message status set to GREEN")
                    self.status = "GREEN"
                    # Reseting the time so that device is ready to send messages
                    if self.config.repeat_alerts:        
                        self.last_msg_time = time.time()-self.config.alert_interval 
                    msg = f"{self.config.good_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
                    self.send_sms(self.config.numbers, msg)
                
                # Send alert if temperature is still high after alert interval
                if cur_time - self.last_msg_time > self.config.alert_interval and self.status == "RED":
                    self.log("Sending High Temperature Message")
                    if not self.config.repeat_alerts:
                        self.last_msg_time = float('inf')  # So that it could never send message again
                    else:
                        self.last_msg_time = time.time()
                    msg = f"{self.config.alert_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
                    self.send_sms(self.config.numbers, msg)
                    
                # Handle changes in power source
                if self.power != self.power_last_state:
                    self.log("Sending power type changed message")
                    if self.power_last_state == "120V-AC":
                        msg = f"{self.config.power_lost_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
                    else:
                        msg = f"{self.config.power_rec_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
                    self.low_battery = False
                    self.send_sms(self.config.numbers, msg)
                    self.power_last_state = self.power
                
                # Case when battery is low 
                if self.power == "UPS":
                    percentage = self.ups.get_battery_level()
                    if percentage <= 80 and self.low_battery == False:
                        self.log("Sending low battery message")
                        msg = f"{self.config.low_battery_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
                        self.send_sms(self.config.numbers, msg)
                        self.low_battery = True
                    
                # Run any scheduled daily status reports
                schedule.run_pending()
            else:
                if self.status == "RED":
                    self.log("System disarmed, resetting status to GREEN")
                    self.status = "GREEN"
            time.sleep(self.check_interval)
            
    def stop(self, block=False):
        """
        Signal the thread to end. Block only if block=True.
        """
        self.end_event.set()
        self.gsm_modem.close()
        if block:
            self.join()
            
    def get_config(self):  
        """
        Get all the config values of the Monitor
        """
        self.config.load_config()
        return {
                "location": self.config.location,
                "temp": self.temp, 
                "max_temp": self.config.max_temp, 
                "hys": self.config.hysteresis, 
                "interval": self.config.alert_interval / 60, 
                "daily_report_time": self.config.daily_report_time,
                "armed": self.config.armed,
                "send_daily_report": self.config.send_daily_report,
                "repeat_alerts": self.config.repeat_alerts,
                "signal_strength": self.gsm_modem.get_signal_strength(), 
                "signal_type": self.gsm_modem.get_network_type(), 
                "pi_time": time.strftime("%B %d  %H:%M"),  
                "numbers": self.config.numbers_list,
                "power": self.power,
                "battery": self.ups.get_battery_level()
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
            msg = f"{self.config.daily_msg}\n\nLocation: {self.config.location}\nTemperature: {self.temp}°C \nTime: {get_rdbl_time()}"
            self.gsm_modem.send_sms_to_many(self.config.daily_numbers, msg)
        
    def send_sms(self, numbers, msg):
        """
        Puts the SMS into queue and writes history
        """
        self.gsm_modem.send_sms_to_many(numbers, msg)
        write_history(msg)
    
    def log(self, message):
        """
        Logs a message if debug mode is enabled
        """
        if self.debug:
            print(message)
            
    def handle_sms(self, sms):
        text = sms.text.lower().strip()
        num = sms.number
        if num in self.config.numbers:  # Check if the message came from the list of numbers in the database
            if text == 'status':  # Same for admin and normal users
                config = self.get_config()
                armed = 'Armed' if config['armed'] else 'Disarmed'
                message = f"Temperature: {config['temp']}°C\nTrigger: {config['max_temp']}°C\nPower: {config['power']}\nArm/Disarm: {armed}"
                self.gsm_modem.send_sms(num, message)
                return

            if text == 'time':  # Same for admin and normal users
                message = f"Time: {get_rdbl_time()}"
                self.gsm_modem.send_sms(num, message)
                return

            if text == 'help':
                help_message = self.config.admin_help if num in self.config.admins else self.config.help   # Seperate for both
                self.gsm_modem.send_sms(num, help_message)
                return

            if num in self.config.admins:  # Additional commands for admin users
                parts = text.split()
                if len(parts) == 3:
                    if parts[0] == 'set' and parts[1] == 'repeat-alerts' and parts[2] in ['on', 'off']:
                        status = parts[2].lower()
                        if status == 'on':
                            update_config(repeat_alerts = True)  
                        else:
                            update_config(repeat_alerts = False)  
                        self.gsm_modem.send_sms(num, f"Repeat-Alerts set to '{status}'.")
                        
                    elif parts[0] == 'set' and parts[1] == 'alert-interval' and is_positive_number(parts[2]):
                        interval = int(parts[2])
                        update_config(interval = interval) 
                        self.gsm_modem.send_sms(num, f"Alert interval set to {interval} minutes.")                       
                        
                    else:
                        self.gsm_modem.send_sms(num, "Invalid value for repeat-alerts. Please enter 'on' or 'off'.")
                    return 
    
            self.gsm_modem.send_sms(num, "Invalid command. Send 'help' for more details.")

            
           
        
if __name__ == "__main__":
    # Create and start a LabMonitor instance for testing
    monitor = LabMonitor(debug=True)
    monitor.start()
    time.sleep(60)  
    monitor.stop()