import serial
import time
import threading
import queue
from utils.file_utils import write_history


class SMSMessage(object):
    def __init__(self, phone_number, message, location, temp):
        self.phone_number = phone_number
        self.message = message
        self.location = location
        self.temp = temp
        
    def __iter__(self):
        return iter((self.phone_number, self.message, self.location, self.temp))

class SIM7600x(threading.Thread):
    def __init__(self, port="/dev/ttyAMA0", debug=False, **kwargs):
        super(SIM7600x, self).__init__(name="SIM7600x", **kwargs)
        
        self.ser = serial.Serial(port, 115200, timeout=5)
        if not self.ser.is_open:
            self.ser.open()
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_queue = queue.Queue() 
        self._signal_lock = threading.Lock()
        self.signal_strength = ""
        self.signal_type= ""
        self.factory_reset()
        self.last_signal_update = time.time()
        self.update_signal_data()
        
    def run(self):
        try:
            self.sms_loop()
        except Exception as err:
            error = str(err) if str(err) else str(err.__class__.__name__)
            self.log("Thread failed: %s" % error)
            self.error = "Unhandled exception: %s" % error
    
    def enqueue_sms(self, numbers, message, location, temp):
        for number in numbers:
            sms = SMSMessage(number, message, location, temp)
            self.sms_queue.put(sms)
        write_history(message, temp, time.time())
                 
    def sms_loop(self):
        while self.end_event.is_set() is False:
            while self.sms_queue.qsize():
                try:
                    sms = self.sms_queue.get_nowait()
                except queue.Empty:
                    break
                self.send_sms(sms)
                
            if self.last_signal_update < time.time()-60:
                self.update_signal_data()
                
    def send_sms(self, sms):
        phone_number, message, location, temp = sms
        try:
            steps = [
            ("AT+CMGF=1", "OK"),
            ('AT+CSCS="GSM"', "OK"),
            (f'AT+CMGS="{phone_number}"', ">")
            ]
            
            for cmd, exp in steps:
                if self.send_at_command(cmd, exp) == "ERROR":
                    self.log(f"Failed at step: {cmd}")
                    return False
                    
            rdble_time = time.strftime("%I:%M %p, %b %d, %Y")
            msg = f"{message}\n\nLocation: {location}\nTemprature: {temp} C \nTime: {rdble_time}"
            
            self.ser.write((msg + '\x1A').encode())
            time.sleep(3)
            response = self.ser.read(self.ser.in_waiting).decode()
            if "+CMGS:" in response:
                self.log(f"Message sent successfully")
                return True
            else:
                self.log(f"Failed to send message")
                return False
            self.factory_reset
        except Exception as e:
            self.log(f"Failed to send message: {e}")
            self.factory_reset()
                            
    def send_at_command(self, command, expected, timeout=1, retries=3):
        self.log(f"Currently running Command: {command}")
        for attempt in range(retries):
            try:
                self.ser.write((command + '\r\n').encode())
                time.sleep(timeout)
                
                response = self.ser.read(self.ser.in_waiting).decode()
              
                if expected in response:
                    self.log("Got expected response")
                    return response
                else:
                    self.log(f"Attempt {attempt + 1}: Expected '{expected}' but got '{response}'")
            except Exception as e:
                self.log(f"Attempt {attempt + 1} failed: {str(e)}")
        return "ERROR"

    def factory_reset(self):
        if self.send_at_command("AT&F", "OK") == "ERROR":
            self.send_at_command('\x1A','')
        else:
            time.sleep(3)
            return
                     
    def log(self, message):
        if self.debug:
            print(message)
    
    def stop(self, block=False):
        """Signal the thread to end. Block only if block=True."""
        self.end_event.set()
        if self.ser.is_open:
            self.ser.close()
            self.log("Serial Port is now closed")
        if block is True:
            self.join() 
    
    def update_signal_data(self):
        self.log("Updating Signal data")
        self.last_signal_update = time.time()
        
        csq_output = self.send_at_command("AT+CSQ", "OK")
        if csq_output == "ERROR":
            new_signal_strength = -1
        else:
            new_signal_strength = self.interpret_signal_quality(csq_output)
        
        cpsi_output = self.send_at_command("AT+CPSI?", "OK")
        if cpsi_output == "ERROR":
            new_signal_type = "X"
        else:
            new_signal_type = self.interpret_network_type(cpsi_output)
        
        with self._signal_lock:
            self._signal_strength = new_signal_strength
            self._signal_type = new_signal_type
        
    def interpret_signal_quality(self, csq_output):
        csq_output = csq_output.split("OK")[0].strip()
        rssi = int(csq_output.split(":")[1].split(",")[0].strip())
        if rssi == 99:
            return 0
        elif rssi >= 0 and rssi <= 9:
            return 1
        elif rssi >= 10 and rssi <= 14:
            return 2
        elif rssi >= 15 and rssi <= 19:
            return 3
        elif rssi >= 20 and rssi <= 31:
            return 4
        else:
            return -1
        
    def interpret_network_type(self, cpsi_output):
        if "Offline" in cpsi_output:
            return "X"
        elif "GSM" in cpsi_output or "EDGE" in cpsi_output:
            return "2G"
        elif "WCDMA" in cpsi_output or "HSDPA" in cpsi_output or "HSUPA" in cpsi_output or "HSPA" in cpsi_output:
            return "3G"
        elif "LTE" in cpsi_output:
            return "4G"
        elif "NR" in cpsi_output:
            return "5G"
        else:
            return "Unknown"
        
    def get_signal_strength(self):
        with self._signal_lock:
            return self._signal_strength

    def get_signal_type(self):
        with self._signal_lock:
            return self._signal_type
                
   
if __name__ == "__main__":
    sms_thread = SIM7600x(debug=True)
    time.sleep(1)
    sms_thread.start()
    sms_thread.enqueue_sms(["+14374293006"], "Alert", "35")
    print(sms_thread.get_signal_strength())
    print(sms_thread.get_signal_type())
    time.sleep(20)
    sms_thread.stop()
    
        
        