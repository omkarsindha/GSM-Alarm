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
