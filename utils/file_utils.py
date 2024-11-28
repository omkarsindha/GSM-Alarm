import os
import json
import time
import traceback

def get_data(file_path="Config/config.json"):
    """
    Get data from Lab Monitor configuration file, returns saved data if file is found 
    or makes a default file and returns default configuration
    """
    default =  {
            "config": {
                "location": "",
                "hysteresis": 1,
                "alert_interval": 2,
                "daily_report_time": "17:30",
                "armed": True,
                "send_daily_report": True,
                "repeat_alerts": True
            },
            "sensors": {},
            "numbers": []
        }
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading file, Path:{file_path} Error: {str(e)}")
        print("Making default file")
        try:
            with open(file_path, 'w') as file:
                json.dump(default, file, indent=4)
        except OSError as e:
            print(f"Error writing default config to file: {str(e)}")
        return default
    
def add_number_to_file(name, number, daily_sms, admin, file_path="Config/config.json"):
    try:
        data = get_data(file_path)
        new_contact = {
            "name": name,
            "number": number,
            "daily_sms": daily_sms,
            "admin": admin
        }
        data["numbers"].append(new_contact)
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error adding number to file: {e}")

def remove_number_by_index(index, file_path="Config/config.json"):
    index -= 1
    try:
        data = get_data(file_path)
        numbers = data["numbers"]
        if 0 <= index < len(numbers):
            numbers.pop(index)
        else:
            print(f"Index {index + 1} is out of range.")

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error removing number by index: {e}")

def update_config(location=None, hys=None, interval=None, daily_report_time=None, send_daily_report=None, armed=None, repeat_alerts=None, file_path="Config/config.json"):
    try:
        data = get_data(file_path)
        config = data["config"]
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
            json.dump(data, file, indent=4)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error updating config: {e}")

def add_new_sensor(sensors, file_path="Config/config.json"):
    """Checks the list of detected sensors,
    ignores if already in the config or will add it to config with defualt values
    """
    data = get_data(file_path)
    sensor_config = data["sensors"]
    
    # Adding if the sensor does not exist
    for sensor in sensors:
        if sensor not in sensor_config:
            sensor_config[sensor] = {"name": "Unknown", "trigger": 99}  # Add default sensor
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error adding new sensor: {e}")

def update_sensor_data(serial, name, trigger, file_path="Config/config.json"):
    """ Edit sensor name and trigger based on sensor serial. """
    data = get_data(file_path)
    sensor_config = data["sensors"]
   
    if serial in sensor_config:
        sensor_config[serial]['name'] = name
        sensor_config[serial]['trigger'] = int(trigger)
        updated_sensor = sensor_config[serial]  # Store the updated sensor
    else:
        updated_sensor = None  # Return None if no matching sensor

    if updated_sensor:
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error updating sensor data: {e}")
    else:
        print("Cannot update, could not find sensor in config")

def write_history(event, file_path="Config/events.json"):
    history = {
        "event": event,
        "time": time.strftime("%I:%M %p, %b %d, %Y")
    } 
    try:
        with open(file_path, "r") as file:
            try:
                history_data = json.load(file)
            except json.JSONDecodeError as e:
                history_data = []
            history_data.append(history)
            with open(file_path, "w") as file:
                json.dump(history_data, file, indent=4)
    except OSError as e:
        print(f"Error writing to history file: {e}")   

def get_history_data(file_path="Config/events.json") -> list[str]: 
    """Get history data"""
    try:
        with open(file_path, 'r') as file:
            history = json.load(file)
            history.reverse()
            return history
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading history data: {e}")
        return []
   
def clear_history(file_path="Config/events.json"):
    try:
        with open(file_path, "w") as file:
            json.dump([], file, indent=4)
    except OSError as e:
        print(f"Error writing to history file: {e}")   
        
if __name__ == '__main__':
    print(get_data(file_path="Config/con.json"))
    print("HI")