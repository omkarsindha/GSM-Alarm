import os
import json
import time 

def write_history(message, filepath="Config/past-alerts.json"):
    history_entry = {
        "message": message,
    }
    
    if os.path.exists(filepath):
        if os.path.getsize(filepath) > 0:  # Check if the file is not empty
            with open(filepath, "r") as file:
                history_data = json.load(file)
        else:
            history_data = []
    else:
        history_data = []

    history_data.append(history_entry)

    with open(filepath, "w") as file:
        json.dump(history_data, file, indent=4)

def get_history_data(file_path="Config/past-alerts.json"):  
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
            history = []
            for entry in data: 
                history.append(entry)
            histor = history.reverse()
            return history
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file: {e}")


def add_contact_to_file(name, number, daily_sms, file_path="Config/numbers.json"):
    with open(file_path, 'r') as file:
        contacts = json.load(file)
    new_contact = {
        "name": name,
        "number": number,
        "daily_sms": daily_sms
    }
    contacts.append(new_contact)
    with open(file_path, 'w') as file:
        json.dump(contacts, file, indent=4)
        
        
def remove_number_by_index(index, file_path="Config/numbers.json"):
    index -= 1
    with open(file_path, 'r') as file:
        contacts = json.load(file)
    if 0 <= index < len(contacts):
        contacts.pop(index)
    else:
        print(f"Index {index + 1} is out of range.")
        return False

    with open(file_path, 'w') as file:
        json.dump(contacts, file, indent=4)
    return True


def update_config(location=None, max_temp=None, hys=None, interval=None, daily_report_time=None, send_daily_report=None, armed=None, repeat_alerts=None, file_path="Config/config.json"):
    with open(file_path, 'r') as file:
        config = json.load(file)
    if location is not None:
        config['location'] = location   
    if max_temp is not None:
        config['max_temp'] = int(max_temp)
    if hys is not None:
        config['hysteresis'] = int(hys)
    if interval is not None:
        config['alert_interval'] = int(interval)
    if daily_report_time is not None:
        config['daily_report_time'] = daily_report_time
    if armed is not None:
        config['armed'] = armed
    if send_daily_report is not None:
        config['send_daily_report'] = send_daily_report
    if repeat_alerts is not None:
        config['repeat_alerts'] = repeat_alerts

    
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)
        
        


