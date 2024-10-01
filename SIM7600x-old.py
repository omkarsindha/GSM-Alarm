import serial
import time
import threading
import queue
from typing import List, Tuple, Optional
import traceback


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
    """
    def __init__(self, parent, port: str = "/dev/ttyAMA0", debug: bool = False, **kwargs):
        super(SIM7600x, self).__init__(name="SIM7600x", **kwargs)
        
        self.parent = parent
        self.ser = serial.Serial(port, 115200, timeout=5)  # Opening serial port at provided port 
        if not self.ser.is_open:
            self.ser.open()
        self.debug = debug
        self.end_event = threading.Event()
        self.sms_queue: queue.Queue = queue.Queue()
        self._signal_lock = threading.Lock()
        self.signal_strength: str = ""
        self.signal_type: str = ""
        self.last_signal_update: float = time.time()
        self.update_signal_data()
        
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
        for number in numbers:
            sms = SMSMessage(number, message)
            self.sms_queue.put(sms)
                 
    def sms_loop(self) -> None:
        """
        Main loop for sending SMS, recieving SMS and updating signal data.
        """
        while not self.end_event.is_set():
            reply = self.send_command('AT&F\r', '\nOK')
            if not (reply.endswith('\nOK') or '\nERROR' in reply):
                self.signal_strength = -1
                self.signal_type = "X"
                self.send_command('\r', '\nOK')
                self.send_command('\032', '\nOK')
                time.sleep(1)
                continue
            
            self.send_command('AT+CMGF=1\r', '\nOK')
            
            reply=self.send_command('AT+CMGL="REC UNREAD"\r', '\nOK')
            print(f"CMGL reply: {reply}")
            if '+CMGL:' in reply:
                parts = reply.split("\n")
                number = parts[1].split(',')[2].strip('"')
                msg = parts[2].strip()
                reply = self.parent.handle_command(msg)
                self.enqueue_sms([number], reply)
                
            if self.last_signal_update < time.time() - 60:
                self.update_signal_data()
                
            while not self.sms_queue.empty():
                try:
                    sms = self.sms_queue.get_nowait()
                except queue.Empty:
                    break
                self.send_sms(sms)
                    
    # def send_sms(self, sms: SMSMessage, retries: int = 3) -> bool:
    #     """
    #     Sends an SMS message with retry logic.
        
    #     :param sms: SMSMessage object containing phone number and message
    #     :param retries: Number of retry attempts
    #     :return: True if message sent successfully, False otherwise
    #     """
    #     phone_number, message = sms
    #     parts = [message[i:i+160] for i in range(0, len(message), 160)] # Splitting the message into 160 character strings if longer than 160 characters
    #     try: 
    #         for i in range(retries):
    #             if 'OK' in self.send_command('AT+CSCS="GSM"\r', '\nOK'):
    #                 if 'OK' in self.send_command('AT+CMGF=1\r', '\nOK'):
    #                     if '\n> ' in self.send_command(f'AT+CMGS="{phone_number}"\r', '\n> '):
    #                         if "\n> " in self.send_command(message + '\r', '\n> '):
    #                             time.sleep(0.5)
    #                             if "+CMGS:" in self.send_command('\032', '\nOK'): 
    #                                 self.log("Message sent successfully")
    #                                 return True
    #             self.log(f"Failed Attempt {i+1}")
    #         self.log("Failed to send message after 3 tries")
    #         return False
    #     except Exception as e:
    #         self.log(f"Failed to send message: {e}")
    #         return False
    
    def send_sms(self, sms: SMSMessage, retries: int = 3) -> bool:
        """
        Sends an SMS message with retry logic and support for concatenated SMS.
        
        :param sms: SMSMessage object containing phone number and message
        :param retries: Number of retry attempts
        :return: True if message sent successfully, False otherwise
        """
        phone_number, message = sms
        pdu_phone = ''.join(['0' + d if i % 2 else d for i, d in enumerate(phone_number[::-1])]) + 'F'
        if len(pdu_phone) % 2 != 0:
            pdu_phone += 'F'

        # Split message into parts
        max_length = 134  # 140 - 6 (UDH length)
        parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        total_parts = len(parts)

        for i, part in enumerate(parts, 1):
            # Construct UDH
            udh = f'050003{i:02X}{total_parts:02X}{i:02X}'

            # Convert message to hex
            hex_message = ''.join([f'{ord(c):02X}' for c in part])

            # Construct PDU
            pdu = (
                '00'  # SMS-SUBMIT
                '41'  # Validity period present
                '00'  # Message Reference (0, let the phone assign)
                f'{len(phone_number):02X}'  # Length of phone number
                '91'  # Type of address (international format)
                f'{pdu_phone}'  # Phone number in PDU format
                '00'  # Protocol identifier
                '08'  # Data coding scheme (Unicode)
                'AA'  # Validity period (4 days)
                f'{math.ceil(len(udh)/2 + len(part)):02X}'  # Length of user data
                f'{udh}{hex_message}'  # UDH + Message
            )

            # Send PDU
            modem.write(f'AT+CMGS={len(pdu)//2 - 1}\r'.encode())
            modem.read_until(b'>')
            modem.write(pdu.encode() + b'\x1A')
            
            response = modem.read_until(b'OK', timeout=10)
            print(f"Part {i}/{total_parts} sent. Response: {response}")

                            
    def send_command(self, command: str, valid_resp: str, timeout: float = 6.0) -> str:
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
        reply = b'\n'.join(lines).decode('latin1')
        self.log(f"Command: {command}, Reply: {reply}")
        return reply
                     
    def log(self, message: str) -> None:
        """
        Logs a message if debug mode is enabled.
        
        :param message: Message to log
        """
        if self.debug:
            print(message)
    
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
        
        csq_output = self.send_command("AT+CSQ\r", "\nOK")
        new_signal_strength = -1 if "ERROR" in csq_output else self.interpret_signal_quality(csq_output)
        
        cpsi_output = self.send_command("AT+CPSI?\r", "\nOK")
        new_signal_type = "X" if cpsi_output == "ERROR" else self.interpret_network_type(cpsi_output)
        
        with self._signal_lock:
            self.signal_strength = new_signal_strength
            self.signal_type = new_signal_type
        
    def interpret_signal_quality(self, csq_output: str) -> int:
        """
        Interprets the signal quality from the CSQ command output.
        
        :param csq_output: Output from the CSQ command
        :return: Interpreted signal strength (0-4) (-1 Means Error)
        """
        if "+CSQ:" in csq_output:
            csq_output = csq_output.split("OK")[0].strip()
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
        
    def interpret_network_type(self, cpsi_output: str) -> str:
        """
        Interprets the network type from the CPSI command output.
        
        :param cpsi_output: Output from the CPSI command
        :return: Interpreted network type
        """
        if "Offline" in cpsi_output:
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
        
    def get_signal_strength(self) -> int:
        """
        Returns the current signal strength.
        
        :return: Current signal strength on range (-1 to 4)
        """
        with self._signal_lock:
            return self.signal_strength

    def get_signal_type(self) -> str:
        """
        Returns the current network type.
        
        :return: Current network type
        """
        with self._signal_lock:
            return self.signal_type
                
   
if __name__ == "__main__":
    sms_thread = SIM7600x(debug=True)
    sms_thread.start()
    sms_thread.enqueue_sms(["+14374293006"], "Alert this is msg")
    #print(sms_thread.get_signal_strength())
    #print(sms_thread.get_signal_type())
    time.sleep(20)
    sms_thread.stop()
    
        
        