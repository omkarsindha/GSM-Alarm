import time
import json

class Config:
    def __init__(self, config_path="Config/config.json", numbers_path="Config/numbers.json"):
        self.max_temp = 0
        self.hysteresis = 0
        self.password = 0
        self.alert_interval = 0
        self.numbers = []
        self.numbers_list = []
        self.alert_msg = 'Alert from GSM Alarm\n\nTemperature is above threshold'
        self.good_msg = 'Alert Resolved\n\nTemperature is now normal :)'
        self.daily_msg = 'Daily Status Report'
        self.daily_report = ''
        self.config_path = config_path
        self.numbers_path = numbers_path
        self.load_config()  

    def load_config(self):
        with open(self.config_path, "r") as file:
            try:
                settings = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")

        self.max_temp = settings.get("max_temp", self.max_temp)
        self.hysteresis = settings.get("hysteresis", self.hysteresis)
        self.password = settings.get("password", self.password)
        self.alert_interval = settings.get("alert_interval", self.alert_interval)*60
        self.daily_report = settings.get("daily_report", "17:00")

        with open(self.numbers_path, "r") as file:
            try:
                self.numbers_list = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")
        self.numbers = [entry["number"] for entry in self.numbers_list]
     


if __name__ == "__main__":
    config_loader = Config()
    print(f"Max Temp: {config_loader.max_temp}")
    print(f"Hysteresis: {config_loader.hysteresis}")
    print(f"Password: {config_loader.password}")
    print(f"Report Interval: {config_loader.alert_interval}")
    print(f"Numbers: {config_loader.numbers}")
    print(f"Daily Stauts Time: {config_loader.daily_report}")
