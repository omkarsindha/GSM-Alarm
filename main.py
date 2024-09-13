from flask_app import app
from LabMonitor import LabMonitor
import signal
import sys

def handle_close_signal(signal, frame):
    print("Stopping monitoring...")
    monitor.stop_monitoring()  # Implement this method to stop the monitoring safely
    print("Stopping Flask app...")
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    sys.exit(0)


if __name__ == '__main__':
        try:
                monitor = LabMonitor()
                monitor.start_monitoring_in_thread()
                signal.signal(signal.SIGINT, handle_close_signal)   # Handle interrupt signal (Ctrl+C)
                signal.signal(signal.SIGTERM, handle_close_signal)  # Handle termination signal (kill command)
                app.run(debug=True, host='0.0.0.0')
        except KeyboardInterrupt:
                monitor.stop_monitoring() 
                print("Program stopped")
                sys.exit(1)
       
    

