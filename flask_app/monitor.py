# flask_app/monitor.py
from LabMonitor import LabMonitor

monitor = None

def init_monitor():
    global monitor
    if monitor is None:
        monitor = LabMonitor(debug=True)
        monitor.start()

def get_monitor():
    return monitor