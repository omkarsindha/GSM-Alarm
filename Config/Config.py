import time
import json

class Config:
    def __init__(self, config_path="Config/config.json", numbers_path="Config/numbers.json"):
        self.location = ""
        self.max_temp = 0
        self.hysteresis = 0
        self.password = 0
        self.alert_interval = 0
        self.armed = False
        self.send_daily_report = False
        self.numbers = []
        self.daily_numbers = []     # Numbers who want daily report sms
        self.numbers_list = []
        self.alert_msg = 'Alert from Lab Monitor\n\nTemperature is above threshold'
        self.good_msg = 'Alert from Lab Monitor\n\nAlert resolved. Temperature is now normal :)'
        self.daily_msg = 'Daily Status Report'
        self.daily_report_time = ''
        self.config_path = config_path
        self.numbers_path = numbers_path
        self.load_config()  

    def load_config(self):
        with open(self.config_path, "r") as file:
            try:
                settings = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")

        self.location = settings.get("location", self.location)
        self.max_temp = settings.get("max_temp", self.max_temp)
        self.hysteresis = settings.get("hysteresis", self.hysteresis)
        self.password = settings.get("password", self.password)
        self.alert_interval = settings.get("alert_interval", self.alert_interval)*60
        self.daily_report_time = settings.get("daily_report_time", "17:00")
        self.armed = settings.get("armed", self.armed)
        self.send_daily_report = settings.get("send_daily_report", self.send_daily_report)

        with open(self.numbers_path, "r") as file:
            try:
                self.numbers_list = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")
        self.numbers = [entry["number"] for entry in self.numbers_list]
        self.daily_numbers = [entry["number"] for entry in self.numbers_list if entry["daily_sms"]]
     


if __name__ == "__main__":
    config_loader = Config()
    print(f"Max Temp: {config_loader.location}")
    print(f"Max Temp: {config_loader.max_temp}")
    print(f"Hysteresis: {config_loader.hysteresis}")
    print(f"Password: {config_loader.password}")
    print(f"Report Interval: {config_loader.alert_interval}")
    print(f"Numbers: {config_loader.numbers}")
    print(f"Numbers List: {config_loader.numbers_list}")
    print(f"Daily Stauts Time: {config_loader.daily_report_time}")
    print(f"Send Daily report?: {config_loader.send_daily_report}")
    print(f"Armed?: {config_loader.armed}")
