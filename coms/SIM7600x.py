import serial
import time
import threading
import queue


class SMSMessage(object):
    def __init__(self, phone_number, message, temp):
        self.phone_number = phone_number
        self.message = message
        self.temp = temp
        
    def __iter__(self):
        return iter((self.phone_number, self.message, self.temp))

class SIM7600x(threading.Thread):
    def __init__(self, port=serial.Serial("/dev/ttyAMA0", 115200, timeout=5), debug=False, **kwargs):
        super(SIM7600x, self).__init__(name="SIM7600x", **kwargs)
        self.ser = port
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_queue = queue.Queue() 
        self.ser.write(("AT&F").encode())
        
    def run(self):
        try:
            self.sms_loop()
        except Exception as err:
            error = str(err) if str(err) else str(err.__class__.__name__)
            self.log("Thread failed: %s" % error)
            self.error = "Unhandled exception: %s" % error
    
    def enqueue_sms(self, numbers, message, temp):
        for number in numbers:
            message = SMSMessage(number, message, temp)
            self.sms_queue.put(message)
                 
    def sms_loop(self):
        while self.end_event.is_set() is False:
            while self.sms_queue.qsize():
                try:
                    sms = self.sms_queue.get_nowait()
                except queue.Empty:
                    break
                self.send_sms(sms)
                
    def send_sms(self, sms):
        phone_number, message, temp = sms
        try:
            steps = [
            ("AT&F", "OK"),
            ("AT+CMGF=1", "OK"),
            ('AT+CSCS="GSM"', "OK"),
            (f'AT+CMGS="{phone_number}"', ">")
            ]
            
            for cmd, exp in steps:
                if not self.send_at_command(cmd, exp):
                    self.log(f"Failed at step: {cmd}")
                    return False
                    
            rdble_time = time.strftime("%B %d %Y %H:%M:%S")
            msg = f"{message}\n\nTemprature: {temp} C \nTime: {rdble_time}"
            
            self.ser.write((msg + '\x1A').encode())
            time.sleep(1)
            
            response = self.ser.read(self.ser.in_waiting).decode()
            if "+CMGS:" in response:
                self.log(f"Message sent successfully")
                return True
            else:
                self.log(f"Failed to send message")
                return False
        
        except Exception as e:
            self.log(f"Failed to send message: {e}")
                            
    def send_at_command(self, command, expected, timeout=1, retries=3):
        self.log(f"Currently running Command: {command}")
        for attempt in range(retries):
            try:
                self.ser.write((command + '\r\n').encode())
                time.sleep(timeout)
                
                response = self.ser.read(self.ser.in_waiting).decode()
              
                if expected in response:
                    return True
                else:
                    self.log(f"Attempt {attempt + 1}: Expected '{expected}' but got '{response}'")
            except Exception as e:
                self.log(f"Attempt {attempt + 1} failed: {str(e)}")
        return False

    def factory_reset(self):
        pass
                
    def log(self, message):
        if self.debug:
            print(message)
    
    def stop(self, block=False):
        """Signal the thread to end. Block only if block=True."""
        self.end_event.set()
        if self.ser.is_open:
            self.ser.close()
            self.log("Serial POrt is now closed")
        if block is True:
            self.join() 
                
   
if __name__ == "__main__":
    sms_thread = SIM7600x(debug=True)
    sms_thread.start()
    sms_thread.enqueue_sms(["+14374293006"], "Alert", "35")
    sms_thread.stop()
    
        
        