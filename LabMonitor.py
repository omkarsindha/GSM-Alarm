from Config.Config import Config
from sensors.TemperatureSensor import TemperatureSensor
from coms.SIM7600x import SIM7600x
import time
import os
import json 
import threading
import schedule
import traceback


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
            self.log(traceback.format_exc())
            
    def monitor_loop(self):
        while self.end_event.is_set() is False:
            if self.config.armed: 
                with self.lock:
                    temp = self.sensor.read_temp()
                    
                current_time = time.time()
                if temp is not None:
                    self.log(f"Current Temperature: {temp}°C")
                    
                    if temp > self.config.max_temp:
                        self.status = "RED"
                        
                    if temp < self.config.max_temp-self.config.hysteresis and self.status == "RED":
                        self.status = "GREEN"
                        self.sms_thread.enqueue_sms(self.config.numbers, self.config.good_msg, self.config.location, temp)
                        
                    if current_time - self.last_msg_time > self.config.alert_interval and self.status == "RED":   
                        self.last_msg_time = time.time()
                        self.log("Sending alert messages...")
                        self.sms_thread.enqueue_sms(self.config.numbers, self.config.alert_msg, self.config.location, temp)
                        
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
        self.config=Config()
        with self.lock:
            temp = self.sensor.read_temp()
        location = self.config.location
        max_temp = self.config.max_temp
        hysteresis = self.config.hysteresis
        alert_interval = self.config.alert_interval/60
        daily_report_time = self.config.daily_report_time
        armed = self.config.armed
        send_daily_report = self.config.send_daily_report
        signal_strength = self.sms_thread.get_signal_strength()
        signal_type = self.sms_thread.get_signal_type()
        pi_time = time.strftime("%B %d  %H:%M")
        numbers = self.config.numbers_list
        return {
                "location": location,
                "temp": temp, 
                "max_temp":max_temp, 
                "hys": hysteresis, 
                "interval": alert_interval, 
                "daily_report_time": daily_report_time,
                "armed": armed,
                "send_daily_report": send_daily_report,
                "signal_strength": signal_strength, 
                "signal_type": signal_type, 
                "pi_time": pi_time,  
                "numbers": numbers
                }
    
    def schedule_daily_status(self):
        self.log(f"Scheduled daily status for {self.config.daily_report_time}")
        schedule.every().day.at(self.config.daily_report_time).do(self.send_daily_status)

    def send_daily_status(self):
        if self.config.send_daily_report:
            self.log("Sent daily status message")
            with self.lock:
                current_temp = self.sensor.read_temp()
            self.sms_thread.enqueue_sms(self.config.daily_numbers, self.config.daily_msg, self.config.location, current_temp)
       
    
    def update_daily_status_schedule(self):
        self.config = Config()
        schedule.clear('daily_status')
        self.schedule_daily_status()
        self.log("Updated daily schedule to new time")
    
if __name__ == "__main__":
    monitor = LabMonitor(debug=True)
    monitor.start()
    time.sleep(60)
    monitor.stop()
        