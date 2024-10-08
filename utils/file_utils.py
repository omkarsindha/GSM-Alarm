import os
import json
import time

def write_history(event, filepath="Config/events.json"):
    history_entry = {
        "event": event,
        "time": time.strftime("%I:%M %p, %b %d, %Y")
    }
    
    try:
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
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error writing history: {e}")

def get_history_data(file_path="Config/events.json"):  
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            history = []
            for entry in data: 
                history.append(entry)
            history.reverse()
            return history
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Error reading history data: {e}")

def get_number_list(file_path="Config/numbers.json"):
    try:
        with open(file_path, 'r') as file:
            numbers = json.load(file)
            return numbers
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Error reading number list: {e}")

def add_number_to_file(name, number, daily_sms, admin, file_path="Config/numbers.json"):
    try:
        with open(file_path, 'r') as file:
            numbers = json.load(file)
        new_contact = {
            "name": name,
            "number": number,
            "daily_sms": daily_sms,
            "admin": admin
        }
        numbers.append(new_contact)
        with open(file_path, 'w') as file:
            json.dump(numbers, file, indent=4)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error adding number to file: {e}")

def remove_number_by_index(index, file_path="Config/numbers.json"):
    index -= 1
    try:
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
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error removing number by index: {e}")
        return False

def update_config(location=None, hys=None, interval=None, daily_report_time=None, send_daily_report=None, armed=None, repeat_alerts=None, file_path="Config/config.json"):
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        if location is not None:
            config['location'] = location   
        if hys is not None:
            config['hysteresis'] = int(hys)
        if interval is not None:
            config['alert_interval'] = int(float(interval))
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
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error updating config: {e}")

def get_config(file_path="Config/config.json"):
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
            return config
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Error reading config: {e}")

def get_sensors(file_path="Config/sensors.json"):
    try:
        with open(file_path, 'r') as file:
            sensors = json.load(file)
            return sensors
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Error reading sensors: {e}")

def add_new_sensor(sensors, file_path="Config/sensors.json"):
    try:
        with open(file_path, 'r') as file:
            sensor_config = json.load(file)
    except (OSError, json.JSONDecodeError) as e:
        sensor_config = {}
    
    # Adding if the sensor does not exist
    for sensor in sensors:
        if sensor not in sensor_config:
            sensor_config[sensor] = {"name": "Unknown", "trigger": 99}  # Add default sensor
    
    try:
        with open(file_path, 'w') as file:
            json.dump(sensor_config, file, indent=4)
    except OSError as e:
        print(f"Error adding new sensor: {e}")

def update_sensor_data(sensor, name, trigger, file_path="Config/sensors.json"):
    """
    Edit sensor name and trigger based on sensor path.
    """
    try:
        with open(file_path, 'r') as file:
            sensor_config = json.load(file)
    except (OSError, json.JSONDecodeError) as e:
        sensor_config = {}
        
    if sensor in sensor_config:
        sensor_config[sensor]['name'] = name
        sensor_config[sensor]['trigger'] = int(trigger)
        updated_sensor = sensor_config[sensor]  # Store the updated sensor
    else:
        updated_sensor = None  # Return None if no matching sensor

    if updated_sensor:
        try:
            with open(file_path, 'w') as file:
                json.dump(sensor_config, file, indent=4)
            return updated_sensor  # Return the updated sensor
        except OSError as e:
            print(f"Error updating sensor data: {e}")
            return None
    else:
        return None  # Return None if no matching sensor
