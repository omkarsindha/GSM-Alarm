from Config.Config import Config
from sensors.TemperatureSensor import TemperatureSensor
from coms.SIM7600x import SIM7600x
import time
import os
import json 
from utils.file_utils import write_history
import threading
import schedule


class LabMonitor(threading.Thread):
    def __init__(self, check_interval=5, debug=False, **kwargs):
        super(LabMonitor, self).__init__(name="Monitor", **kwargs)
        self.config = Config(config_path="Config/config.json")
        self.sensor = TemperatureSensor()
        self.check_interval = check_interval
        self.last_msg_time = time.time() - self.config.alert_interval
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_thread = SIM7600x(debug=debug)
        self.sms_thread.start()
        self.lock = threading.Lock()
        self.log("Initiated an instance of monitor thread")
        self.schedule_daily_status()
        
    def run(self):
        try:
            self.monitor_loop()
        except Exception as err:
            error = str(err) if str(err) else str(err.__class__.__name__)
            self.log("Thread failed: %s" % error)
            self.error = "Unhandled exception: %s" % error

    def monitor_loop(self):
        while self.end_event.is_set() is False:
            with self.lock:
                temp = self.sensor.read_temp()
            current_time = time.time()
            if temp is not None:
                self.log(f"Current Temperature: {temp}°C")
                if temp > self.config.max_temp and (current_time - self.last_msg_time > self.config.alert_interval):   
                    self.last_msg_time = time.time()
                    self.log("Sending alert messages...")
                    self.sms_thread.enqueue_sms(self.config.numbers, self.config.alert_msg, temp)
                    write_history(self.config.alert_msg, temp, current_time)
            else:
                self.log("Error reading temprature")  
                 
            schedule.run_pending()
            time.sleep(self.check_interval) 
        
    def log(self, message):
        if self.debug:
            print(message)
            
    def stop(self, block=False):
        """Signal the thread to end. Block only if block=True."""
        self.end_event.set()
        self.sms_thread.stop()
        if block is True:
            self.join()
            
    def get_config(self):
        self.config = Config()
        with self.lock:
            current_temp = self.sensor.read_temp()
        numbers = self.config.numbers_list
        max_temp = self.config.max_temp
        hysteresis = self.config.hysteresis
        alert_interval = self.config.alert_interval
        return current_temp, max_temp, hysteresis, alert_interval, numbers
    
    def schedule_daily_status(self):
        try:
            schedule.every().day.at(self.config.daily_status_time).do(self.send_daily_status)
            self.log(f"Scheduled daily status for {self.config.daily_status_time}")
        except Exception as e:
            self.log(f"Error scheduling daily status: {str(e)}. Using default time 12:00.")
            schedule.every().day.at("12:00").do(self.send_daily_status)

    def send_daily_status(self):
        with self.lock:
            current_temp = self.sensor.read_temp()
        self.sms_thread.enqueue_sms(self.config.numbers, self.config.daily_msg, current_temp)
        self.log("Sent daily status message")
    
    
if __name__ == "__main__":
    monitor = LabMonitor(debug=True)
    monitor.start()
    time.sleep(60)
    monitor.stop()
        