import serial
import time
import threading
import queue
import traceback
import gsmmodem
from systemd import journal
import traceback


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
        
        self.modem = gsmmodem.modem.GsmModem(port, 115200, smsReceivedCallbackFunc=parent.handle_sms)
        self.modem.connect(None,5)
        self.log("Now connected to GSM modem")
        
        self.signal_strength: int = self.cur_signal_strength()         # Signal strength on scale of 1 to 4 or -1 in case of error
        self.network_type: str = self.cur_network_type()               # Network type i.e 2G, 3G, 4G ...
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
        Main loop for sending SMS and updating signal data.
        """
        while not self.end_event.is_set():      
            while not self.sms_queue.empty():
                try:
                    number, msg = self.sms_queue.get_nowait()
                    self.send_sms(number, msg)
                except queue.Empty:
                    break
            
            if self.last_update < time.time() - 60:
                self.signal_strength = self.cur_signal_strength()
                self.network_type = self.cur_network_type()       
                self.last_update = time.time() 
                         
    def enqueue_sms(self, numbers: list[str], message: str) -> None:
        """
        Enqueue the same message for a list of numbers partitions message if it is too long 
        """
        # Converting one message into mulitple if it is long
        self.log(f"Sending messages to {numbers} Text:")
        message_parts = self.partition_message(message)
        self.log('+\n'.join(message_parts))
        for number in numbers:
            for msg in message_parts:
                self.sms_queue.put((number, msg))
    
    def send_sms(self, phone_number: str, message: str, retries=3, delay=2) -> None:
        """
        Calls the sendSms function of the GSM modem library, re-sends message 3 times before failing.
        """
        try:
            self.modem.sendSms(phone_number, message)
            self.log(f'SMS Sent to {phone_number}.')
        except gsmmodem.exceptions.TimeoutException as e:
            self.log(f"Failed to send message to {phone_number}: {str(e)}.")
            self.log(traceback.format_exc())
            
        # for i in range(retries):
        #     try:
        #         self.modem.sendSms(phone_number, message)
        #     except gsmmodem.exceptions.TimeoutException as e:
        #         self.log(f"Failed to send message to {phone_number}: {str(e)}. Attempt {i+1}")
        #         time.sleep(delay)
        #     else:
        #         self.log(f'SMS Sent to {phone_number}.')
        #         break
        # else:
        #     self.log(f"Failed to send message to {phone_number} after {retries} attempts.")
     
    def cur_signal_strength(self) -> int:
        """
        Interprets the signal quality from the CSQ command output.
        
        :return: Interpreted signal strength on a scale of 0-4 
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
                    return 0
            else:
                return 0
        except Exception as e:
            self.log(f"Failed to get signal strength: {e}")
            return 0
        
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
                return "X"
        except Exception as e:
            self.log(f"Failed to get network type: {e}")
            return "X"

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
            journal.send(message)

    def partition_message(self, msg: str, max_length: int= 155, min_length: int = 130) -> list[str]:
        """Partition long messages into parts breaks the message at \n or space just before max_length.
    
        Parameters:
        msg (str): The long message to be partitioned.
        max_length (int): The maximum length of each partition.
        min_length (int): The minimum length to start looking for a newline or space. 
        """
        parts = []
        start = 0

        while start < len(msg):
            end = min(start + max_length, len(msg))
            # Try to find a \n between min_length and max_length
            newline_pos = msg.rfind('\n', start + min_length, end)
            if newline_pos != -1:
                parts.append(msg[start:newline_pos])
                start = newline_pos + 1
            else:
                # If no \n is found find the last space within the range
                space_pos = msg.rfind(' ', start + min_length, end)
                if space_pos != -1:
                    parts.append(msg[start:space_pos])
                    start = space_pos + 1
                else:
                    parts.append(msg[start:end]) # If no space is found break at max_length
                    start = end

        return parts


if __name__ == "__main__":
    sms = SIM7600x(debug=True)
    sms.start()
    sms.enqueue_sms(["+14374293006"], "Hello message")
    time.sleep(100)
    sms.stop()
