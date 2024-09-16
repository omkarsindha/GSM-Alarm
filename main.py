from flask_app import app
from LabMonitor import LabMonitor
import signal
import sys

if __name__ == '__main__':
        def shutdown_server():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
    
        try:
            monitor = LabMonitor(debug=True)
            monitor.start()
            app.run(debug=True, host='0.0.0.0')
        except KeyboardInterrupt:
            monitor.stop() 
            shutdown_server()
            print("Program stopped")
            sys.exit(1)
       
    

