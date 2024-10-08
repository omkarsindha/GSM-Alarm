import serial
import time
import threading
import queue
from typing import List, Tuple, Optional
import traceback
from gsmmodem.modem import GsmModem, SentSms
from gsmmodem.exceptions import TimeoutException

class SIM7600x(threading.Thread):
    """
    A class to interact with the SIM7600x modem for sending SMS messages and monitoring signal strength.
    Runs as a separate thread. 
    Parent should have a handle_sms(sms) function to have customizable replies to sms
    """
    def __init__(self, parent=None, port: str = "/dev/ttyAMA0", debug: bool = False, **kwargs):
        super(SIM7600x, self).__init__(name="SIM7600x", **kwargs)
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_queue: queue.Queue = queue.Queue()
        self.signal_strength = 0
        self.network_type: str = ""
        self.lock = threading.Lock()
        
        self.modem = GsmModem(port, 115200, smsReceivedCallbackFunc=parent.handle_sms)
        self.modem.connect(None)
        self.log("Now connected to GSM modem")
        self.modem.write("AT+CMGD=1,4")   # Delete all received messages before starting
        self.signal_strength = self.cur_signal_strength()
        self.network_type = self.cur_network_type()   
        self.last_update: float = time.time()
          
    def run(self) -> None:
        """ Main thread function, runs the SMS loop"""
        while not self.end_event.is_set():
            try:
                self.sms_loop()
            except Exception as err:
                error = str(err) if str(err) else str(err.__class__.__name__)
                self.log(f"Thread encountered an error: {error}")
                self.log(traceback.format_exc())
                time.sleep(5)  # Sleep for a while before retrying

    def sms_loop(self) -> None:
        """
        Main loop for sending SMS, receiving SMS and updating signal data.
        """
        while not self.end_event.is_set():     
            if self.last_update < time.time() - 60:
                self.signal_strength = self.cur_signal_strength()
                self.network_type = self.cur_network_type()       
                self.last_update = time.time() 
            while not self.sms_queue.empty():
                try:
                    number, msg = self.sms_queue.get_nowait()
                    self.send_sms(number, msg)
                except queue.Empty:
                    break
                except Exception as e:
                    self.log(f"Failed to send SMS: {e}")
                         
    def enqueue_sms(self, numbers: List[str], message: str) -> None:
        """
        Enqueue the same message for a list of numbers 
        """
        for number in numbers:
            self.sms_queue.put((number, message))
    
    def send_sms(self, phone_number: str, message: str):
        """
        Calls the sendSms function of the GSM modem library
        """
        self.log(f"Sending message to {phone_number} Text:")
        self.log(message)
        try:
            self.modem.sendSms(phone_number, message)
        except TimeoutException as e:
            self.log(f"Failed to send message to {phone_number}: {e}")
            return
        self.log('SMS Sent.')
     
    def cur_signal_strength(self) -> int:
        """
        Interprets the signal quality from the CSQ command output.
        
        :return: Interpreted signal strength on a scale of 0-4 (-1 Means Error)
        """
        try:
            csq_output = self.modem.write("AT+CSQ")[0]
            if "+CSQ:" in csq_output:
                rssi = int(csq_output.split(":")[1].split(",")[0].strip())
                if rssi == 99:
                    return 0
                elif 3 <= rssi <= 9:
                    return 1
                elif 10 <= rssi <= 14:
                    return 2
                elif 15 <= rssi <= 19:
                    return 3
                elif 20 <= rssi <= 31:
                    return 4
                else:
                    return -1
            else:
                return -1
        except Exception as e:
            self.log(f"Failed to get signal strength: {e}")
            return -1
        
    def cur_network_type(self) -> str:
        """
        Interprets the Network Type from the CPSI command output.
        
        :return: Interpreted Network Type i.e 2G, 3G, 4G or 5G, X means no service
        """
        try:
            cpsi_output = self.modem.write("AT+CPSI?")[0]
            if "NO SERVICE" in cpsi_output or "OFFLINE" in cpsi_output:
                return "X"
            elif "GSM" in cpsi_output or "EDGE" in cpsi_output:
                return "2G"
            elif any(tech in cpsi_output for tech in ["WCDMA", "HSDPA", "HSUPA", "HSPA"]):
                return "3G"
            elif "LTE" in cpsi_output:
                return "4G"
            elif "NR" in cpsi_output:
                return "5G"
            else:
                return "Unknown"
        except Exception as e:
            self.log(f"Failed to get network type: {e}")
            return "Unknown"

    def stop(self, block: bool = False) -> None:
        """
        Signals the thread to stop and optionally waits for it to finish.
        
        :param block: If True, waits for the thread to finish
        """
        self.end_event.set()
        self.modem.close()        
        self.log("Connection to GSM modem closed")
        if block:
            self.join() 
    
    def log(self, message: str) -> None:
        """
        Logs a message if debug mode is enabled.
        
        :param message: Message to log
        """
        if self.debug:
            print(message)
   
if __name__ == "__main__":
    sms = SIM7600x(debug=True)
    sms.start()
    sms.enqueue_sms(["+14374293006"], "Simple message")
    time.sleep(100)
    sms.stop()
