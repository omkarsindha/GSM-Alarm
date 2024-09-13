from Config.Config import Config
from sensors.TemperatureSensor import TemperatureSensor
from coms.SIM7600x import SIM7600x
import time
import os
import json 
from utils.file_utils import write_history
import threading


class LabMonitor:
    def __init__(self, check_interval=5):
        self.history = "Config/past-alerts.json"
        self.config = Config(config_path="Config/config.json")
        self.sensor = TemperatureSensor()
        self.sim7600x = SIM7600x()
        self.check_interval = check_interval
        self.last_msg_time = time.time() - self.config.report_interval
        

    def monitor_temperature(self):
        while True:
            temp = self.sensor.read_temp()
            current_time = time.time()
            if temp is not None:
                print(f"Current Temperature: {temp}°C")
                if temp > self.config.max_temp and (current_time - self.last_msg_time > self.config.report_interval):   
                    self.last_msg_time = time.time()
                    print("Sending alert messages...")
                    self.sim7600x.send_sms_in_thread(self.config.numbers, self.config.message, temp)
                    write_history(self.history, self.config.message, temp, current_time)
            else:
                print("Error reading temprature")
                
            time.sleep(self.check_interval)
        
        
    def start_monitoring_in_thread(self):
        monitor_thread = threading.Thread(target=self.monitor_temperature)
        monitor_thread.start()
    
if __name__ == "__main__":
    monitor = LabMonitor()
    try:
        monitor.monitor_temperature()
    except KeyboardInterrupt:
        print("Monitoring stopped.")
        
        