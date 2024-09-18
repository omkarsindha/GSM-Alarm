from LabMonitor import LabMonitor
from flask import current_app

def get_monitor():
    if 'monitor' not in current_app.config:
        current_app.config['monitor'] = LabMonitor(debug=True)
    return current_app.config['monitor']

def start_monitor():
    monitor = get_monitor()
    monitor.start()
    print("Monitor started")

def stop_monitor():
    monitor = get_monitor()
    monitor.stop()
    print("Monitor stopped")