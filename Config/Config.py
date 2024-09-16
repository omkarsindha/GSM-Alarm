import time
import json

class Config:
    def __init__(self, config_path="Config/config.json", numbers_path="Config/numbers.json"):
        self.max_temp = 0
        self.hysteresis = 0
        self.password = 0
        self.report_interval = 0
        self.numbers = []
        self.message = ''
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
        self.report_interval = settings.get("report_interval", self.report_interval)
        self.message = settings.get("message", self.message)

        with open(self.numbers_path, "r") as file:
            try:
                numbers_list = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")
        self.numbers = [entry["number"] for entry in numbers_list]

        




if __name__ == "__main__":
    config_loader = Config()
    print(f"Max Temp: {config_loader.max_temp}")
    print(f"Hysteresis: {config_loader.hysteresis}")
    print(f"Password: {config_loader.password}")
    print(f"Report Interval: {config_loader.report_interval}")
    print(f"Numbers: {config_loader.numbers}")
