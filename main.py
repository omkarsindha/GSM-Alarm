from flask_app import app
from LabMonitor import LabMonitor
import signal
from flask import Flask, request
import os
from monitor_instance import start_monitor, get_monitor, stop_monitor


if __name__ == '__main__':
    with app.app_context():
        try:
            start_monitor()
            app.run(host='127.0.0.1', debug=True, use_reloader=False, port=5000)
        finally:
            stop_monitor()
            print("Program stopped")
        

       
    

