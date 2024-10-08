import time
import json
from utils.file_utils import get_config, get_number_list, get_sensors


class Config:
    def __init__(self, config_path="Config/config.json", numbers_path="Config/numbers.json"):
        self.location = ""
        self.hysteresis = 0             # After reaching max temp device sends msg till drops below max temp - hys   
        self.alert_interval = 0
        self.armed = False              # On or Off
        self.send_daily_report = False
        self.repeat_alerts = False
        self.numbers = []               # Acutal phone number list
        self.daily_numbers = []         # Phone Numbers who want daily report sms
        self.numbers_list = []          # Phone Number object's list
        self.daily_report_time = ''
        self.config_path = config_path
        self.numbers_path = numbers_path
        self.load_config()  

    def load_config(self):
        config = get_config()
        self.location = config.get("location", self.location)
        self.hysteresis = config.get("hysteresis", self.hysteresis)
        self.alert_interval = config.get("alert_interval", self.alert_interval)*60
        self.daily_report_time = config.get("daily_report_time", "17:00")
        self.armed = config.get("armed", self.armed)
        self.send_daily_report = config.get("send_daily_report", self.send_daily_report)
        self.repeat_alerts = config.get("repeat_alerts", self.repeat_alerts)
        
        self.numbers_list = get_number_list()
        self.numbers = [entry["number"] for entry in self.numbers_list]
        self.daily_numbers = [entry["number"] for entry in self.numbers_list if entry["daily_sms"]]
        self.admins = [entry["number"] for entry in self.numbers_list if entry["admin"]]

        self.sensors = get_sensors()

if __name__ == "__main__":
    config_loader = Config()
    print(f"Loc: {config_loader.location}")
    print(f"Hysteresis: {config_loader.hysteresis}")
    print(f"Password: {config_loader.password}")
    print(f"Report Interval: {config_loader.alert_interval}")
    print(f"Numbers: {config_loader.numbers}")
    print(f"Numbers List: {config_loader.numbers_list}")
    print(f"Daily Stauts Time: {config_loader.daily_report_time}")
    print(f"Send Daily report?: {config_loader.send_daily_report}")
    print(f"Armed?: {config_loader.armed}")
