from flask_app import app
from LabMonitor import LabMonitor
import signal
from flask import Flask, request
import os
from monitor_instance import start_monitor, get_monitor, stop_monitor



if __name__ == '__main__':
    with app.app_context():
        try:
            if not os.environ.get('WERKZEUG_RUN_MAIN'):
                start_monitor()
            app.run(host='0.0.0.0', debug=True, use_reloader=False)#use_reloader=False
        except KeyboardInterrupt:
            pass
        finally:
            stop_monitor()
            print("Program stopped")
        

       
    

