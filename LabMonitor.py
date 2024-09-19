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
        self.schedule_daily_status()
        self.status = "GREEN"
        self.log("Initiated an instance of monitor thread")
         
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
                
                if temp > self.config.max_temp:
                    self.status = "RED"
                    
                if temp < self.config.max_temp-self.config.hysteresis and self.status == "RED":
                    self.status = "GREEN"
                    self.sms_thread.enqueue_sms(self.config.numbers, self.config.good_msg, temp)
                    
                if current_time - self.last_msg_time > self.config.alert_interval and self.status == "RED":   
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
        self.update_daily_status_schedule()
        with self.lock:
            current_temp = self.sensor.read_temp()
        numbers = self.config.numbers_list
        max_temp = self.config.max_temp
        hysteresis = self.config.hysteresis
        alert_interval = self.config.alert_interval/60
        daily_report = self.config.daily_report
        return current_temp, max_temp, hysteresis, alert_interval, daily_report, numbers
    
    def schedule_daily_status(self):
        schedule.every().day.at(self.config.daily_report).do(self.send_daily_status)
        self.log(f"Scheduled daily status for {self.config.daily_report}")
    

    def send_daily_status(self):
        with self.lock:
            current_temp = self.sensor.read_temp()
        self.sms_thread.enqueue_sms(self.config.numbers, self.config.daily_msg, current_temp)
        self.log("Sent daily status message")
    
    def update_daily_status_schedule(self):
        schedule.clear('daily_status')
        self.schedule_daily_status()
        self.log("Updated daily schedule to new time")
    
if __name__ == "__main__":
    monitor = LabMonitor(debug=True)
    monitor.start()
    time.sleep(60)
    monitor.stop()
        