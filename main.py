from flask_app import app
from LabMonitor import LabMonitor
import signal
from flask import Flask, request
import os


monitor = None
def start_monitor():
    global monitor
    if monitor is None:
        monitor = LabMonitor(debug=True)
        monitor.start()
        print("Monitor started")

if __name__ == '__main__':
    try:
        if not os.environ.get('WERKZEUG_RUN_MAIN'):
            start_monitor()
            app.config['monitor'] = monitor
            print(monitor)
        app.run(debug=True, host='0.0.0.0')
    except KeyboardInterrupt:
        pass
    finally:
        if monitor is not None:
            monitor.stop()
        print("Program stopped")
        

       
    

