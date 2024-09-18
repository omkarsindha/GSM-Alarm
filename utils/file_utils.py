import os
import json

def write_history(message, temp, date, filepath="Config/past-alerts.json"):
    history_entry = {
        "message": message,
        "temperature": temp,
        "time": date
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


def add_contact_to_file(name, number, file_path="Config/numbers.json"):
    with open(file_path, 'r') as file:
        contacts = json.load(file)
    
    new_contact = {
        "name": name,
        "number": number
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


def update_config(max_temp=None, hys=None, interval=None, file_path="Config/config.json"):
    with open(file_path, 'r') as file:
        config = json.load(file)
        
    if max_temp is not None:
        config['max_temp'] = int(max_temp)
    if hys is not None:
        config['hysteresis'] = int(hys)
    if interval is not None:
        config['alert_interval'] = int(interval)
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)