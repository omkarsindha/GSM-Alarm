import serial
import time
import threading
import queue
from typing import List, Tuple, Optional
import traceback
from systemd import journal

class SMSMessage:
    """ Represents an SMS message """
    def __init__(self, phone_number: str, message: str):
        self.phone_number = phone_number
        self.message = message
        
    def __iter__(self) -> iter:
        """Used to directly unpack an object"""
        return iter((self.phone_number, self.message))

class SIM7600x(threading.Thread):
    """
    A class to interact with the SIM7600x modem for sending SMS messages and monitoring signal strength.
    Runs as a separate thread.
    According to the PI you are using, the user UART device of Raspberry Pi 2B/Zero is ttyAMA0, and ttyS0 of Raspberry Pi 3B.
    """
    def __init__(self, parent, port: str = "/dev/ttyS0", debug: bool = False, **kwargs):
        super(SIM7600x, self).__init__(name="SIM7600x", **kwargs)
        
        self.parent = parent
        self.ser = serial.Serial(port, 115200, timeout=5)  # Opening serial port at provided port 
        if not self.ser.is_open:
            self.ser.open()
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_queue: queue.Queue = queue.Queue()
        self.failed_sms_list: list[SMSMessage] = []
        
        self.signal_strength: str = ""
        self.network_type: str = ""
        self.last_signal_update: float = time.time()
        self.update_signal_data()
        self.send_command('AT+CPMS="SM","SM","SM"\r', 'OK')  # Set SMS storage to SIM 
        self.send_command('AT+CMGD=1,4\r', 'OK')             # Delete all messages
        
    def run(self) -> None:
        """ Main thread function, runs the SMS loop"""
        try:
            self.sms_loop()
        except Exception as err:
            error = str(err) if str(err) else str(err.__class__.__name__)
            self.log(f"Thread failed: {error}")
            self.error = f"Unhandled exception: {error}"
            self.log(traceback.format_exc())
    
    def enqueue_sms(self, numbers: List[str], message: str) -> None:
        """
        Enqueues SMS messages for multiple recipients.
        
        :param numbers: List of phone numbers to send the message to
        :param message: The message content
        """
         # Converting one message into mulitple if it is long
        self.log(f"Sending messages to {numbers} Text:")
        self.log(message)
        message_parts = self.partition_message(message)
        for number in numbers:
            for msg in message_parts:
                self.sms_queue.put((number, msg))
        # self.log(f"This is queue now {self.sms_queue}")
                 
    def sms_loop(self) -> None:
        """
        Main loop for sending SMS, recieving SMS and updating signal data.
        """
        while not self.end_event.is_set():
            reply = self.send_command('AT&F\r', 'OK')
            if not (reply.endswith('OK') or 'ERROR' in reply):
                self.signal_strength = 0
                self.network_type = "NO SERVICE"
                self.send_command('\r', 'OK')
                self.send_command('\032', 'OK')
                time.sleep(1)
                continue
        
            if self.last_signal_update < time.time() - 10 or self.network_type =="NO SERVICE":
                self.update_signal_data()
                if self.network_type == "NO SERVICE":
                    continue
                                    
            self.check_recieved_sms()
            
            while not self.sms_queue.empty():
                try:
                    sms = self.sms_queue.get_nowait()
                except queue.Empty:
                    break
                self.send_sms(sms)
                
            # if network is online, check for failed messages  
            # if self.network_type != "NO SERVICE": 
            #     temp_list = []
            #     for sms in self.failed_sms_list:
            #         if not self.send_sms(sms): # Failed to send message
            #             temp_list.append(sms)
            #     self.failed_sms_list = temp_list
                    
    def send_sms(self, sms: SMSMessage, retries: int = 3) -> bool:
        """
        Sends an SMS message with retry logic.
        
        :param sms: SMSMessage object containing phone number and message
        :param retries: Number of retry attempts
        :return: True if message sent successfully, False otherwise
        """   
        phone_number, message = sms
        parts = [message[i:i+160] for i in range(0, len(message), 160)] # Splitting the message into 160 character strings if longer than 160 characters
        try: 
            for i in range(retries):
                if 'OK' in self.send_command('AT+CSCS="GSM"\r', 'OK'):
                    if 'OK' in self.send_command('AT+CMGF=1\r', 'OK'):
                        if '>' in self.send_command(f'AT+CMGS="{phone_number}"\r', '>'):
                            if '+CMGS:' in self.send_command(f'{message}\r\032', 'OK', timeout=90.0):
                                self.log("Message sent successfully")
                                return True
                self.log(f"Failed Attempt {i+1}")
            self.log("Failed to send message after 3 tries")
            return False
        except Exception as e:
            self.log(f"Failed to send message: {e}")
            return False
                            
    def send_command(self, command: str, valid_resp: str, timeout: float = 10.0) -> str:
        """
        Sends a command to the modem and waits for a valid response.
        
        :param command: Command to send
        :param valid_resp: Expected valid response
        :param timeout: Timeout for waiting for response
        :return: Decoded response from the modem
        """
        if not self.ser.isOpen():
            self.ser.open()
        if self.ser.timeout != timeout:
            self.ser.timeout = timeout
            
        command = bytes(command, encoding="ascii", errors='replace')
        valid_resp = bytes(valid_resp, encoding="ascii", errors="replace")

        self.ser.write(command)
        time.sleep(1)
        try:
            data = self.ser.read_until(valid_resp)
        except OSError:
            data = b""

        lines = data.splitlines()
        if lines and lines[0] == command.strip(b'\r\n'):
            lines = lines[1:]
        if len(lines) > 1 and not lines[0] and lines[1] == command.strip(b'\r\n'):
            lines = lines[2:]
        reply = b'\n'.join(lines).decode('latin1').strip()
        self.log(f"Command: {command}, Reply: {reply}")
        return reply
    
    def check_recieved_sms(self):
        self.send_command('AT+CMGF=1\r', 'OK')
        
        reply=self.send_command('AT+CMGL="REC UNREAD"\r', 'OK')
        # Example message in modem:  +CMGL: 1,"REC READ","+123","","24/10/17,12:14:52-16" \nThis is a simple message 
        if '+CMGL:' in reply:
            lines = reply.split("\n")
            for i in range(len(lines)):
                if '+CMGL:' in lines[i]:
                    details = lines[i].replace('"', '').split(',')
                    if len(details) >= 3:
                        index = details[0].replace('+CMGL: ', '')
                        number = details[2]
                        message = lines[i+1].strip()
                        
                        self.log(f"Recieved message from {number}: {message}")
                        response = self.parent.handle_message(number,message)
                        if response:
                            self.enqueue_sms([number], response)
                        else:
                            self.log(f"Unknown messager {number}")
                            
                        self.send_command(f'AT+CMGD={index}\r', 'OK')   # Delete the message after reading it


                     
    def log(self, message: str) -> None:
        """
        Logs a message if debug mode is enabled.
        
        :param message: Message to log
        """
        if self.debug:
            journal.send(message)
    
    def stop(self, block: bool = False) -> None:
        """
        Signals the thread to stop and optionally waits for it to finish.
        
        :param block: If True, waits for the thread to finish
        """
        self.end_event.set()
        if self.ser.is_open:
            self.ser.close()
            self.log("Serial Port is now closed")
        if block:
            self.join() 
    
    def update_signal_data(self) -> None:
        """
        Updates the signal strength and network type data.
        """
        self.log("Updating Signal data")
        self.last_signal_update = time.time()
        
        csq_output = self.send_command("AT+CSQ\r", "OK")
        self.signal_strength = self.interpret_signal_strength(csq_output)
        
        cpsi_output = self.send_command("AT+CPSI?\r", "OK")
        self.network_type = self.interpret_network_type(cpsi_output)
        
    def interpret_signal_strength(self, csq_output: str) -> int:
        """
        Interprets the signal quality from the CSQ command output.
        
        :param csq_output: Output from the CSQ command
        :return: Interpreted signal strength (0-4) (0 Means Error reading signal strength)
        """
        try:
            if "+CSQ:" in csq_output:
                csq_output = csq_output.split("OK")[0].strip()
                rssi = int(csq_output.split(":")[1].split(",")[0].strip())
                if rssi == 99:
                    return 0
                elif 0 <= rssi <= 31:
                    return rssi
                else:
                    return 0
            else:
                return 0
        except Exception as e:
            self.log(f"Error while interpreting signal strength: {e}")
            return 0
        
    def interpret_network_type(self, cpsi_output: str) -> str:
        """
        Interprets the network type from the CPSI command output. i.e 2G, 3G, 4G or X in case not registered to network
        
        :param cpsi_output: Output from the CPSI command
        :return: Interpreted network type
        """
        if "NO SERVICE" in cpsi_output or "OFFLINE" in cpsi_output or "ERROR" in cpsi_output:
                return "NO SERVICE"
        elif "GSM" in cpsi_output or "EDGE" in cpsi_output:
            return "2G"
        elif any(tech in cpsi_output for tech in ["WCDMA", "HSDPA", "HSUPA", "HSPA"]):
            return "3G"
        elif "LTE" in cpsi_output:
            return "4G"
        elif "NR" in cpsi_output:
            return "5G"
        else:
            return "NO SERVICE"
        
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
    sms_thread = SIM7600x(debug=True)
    sms_thread.start()
    sms_thread.enqueue_sms(["+14374293006"], "Alert this is msg")
    #print(sms_thread.get_signal_strength())
    #print(sms_thread.get_network_type())
    time.sleep(20)
    sms_thread.stop()
    
        
        
