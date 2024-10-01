import serial
import time
import threading
import queue
from typing import List, Tuple, Optional
import traceback
from gsmmodem.modem import GsmModem


class SIM7600x():
    """
    A class to interact with the SIM7600x modem for sending SMS messages and monitoring signal strength.
    Runs as a separate thread.
    """
    def __init__(self, parent, port: str = "/dev/ttyAMA0", debug: bool = False):
        self.modem = GsmModem(port, 115200, smsReceivedCallbackFunc=parent.handle_sms)
        self.modem.smsTextMode = False
        self.debug = debug
    
    def connect(self):
        self.modem.connect()
        self.log("Now connected to GSM modem")
        
    def send_sms_to_many(self, numbers: List[str], message: str) -> None:
        for number in numbers:
            self.send_sms(number, message)
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        self.log(f"Sending message to {phone_number} Text:")
        self.log(message)
        encoded_message = message.encode('utf-16-be').hex().upper()
        self.modem.sendSms(phone_number, encoded_message)
        self.log('Message sent successfully')    
        
             
    def handle_sms(self, sms) :
        if sms.text.lower().strip() == 'help':
            self.send_sms_to_many([sms.number], "Lab Monitor ⚙️\n1. status\n2. set trigger [value]\n3. set repeat-alerts [on/off]\n4. set alarm [on/off]")
            return
        
        parts = sms.text.lower().split()
        if len(parts) == 3:
            if parts[0] == 'set':
                if parts[1] == 'trigger':
                    try:
                        trigger = float(parts[2])
                        print(f"Trigger temperature set to: {trigger}")
                    except ValueError:
                        print("Invalid value for trigger. Please enter a number.")
                elif parts[1] == 'status':
                    if parts[2].lower() in ['on', 'off']:
                        status = parts[2].lower()
                        print(f"Sensor status set to: {status}")
                    else:
                        print("Invalid value for status. Please enter 'on' or 'off'.")
                elif parts[1] == 'repeat-alerts':
                    try:
                        repeat_alerts = int(parts[2])
                        print(f"Repeat alerts interval set to: {repeat_alerts} minutes")
                    except ValueError:
                        print("Invalid value for repeat-alerts. Please enter an integer.")
                else:
                    print("Invalid configuration type. Please use 'trigger', 'status', or 'repeat-alerts'.")
            else:
                print("Invalid command. Please start with 'set'.")
        else:
            print("Invalid command format. Please use the format: set [type] [value]")
        
    def close(self):
        self.modem.close()        
        self.log("Connection to GSM modem closed")
        
    def get_signal_strength(self) -> int:
        """
        Interprets the signal quality from the CSQ command output.
        
        :param csq_output: Output from the CSQ command
        :return: Interpreted signal strength on a scale of 0-4 (-1 Means Error)
        """
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
        
    def get_network_type(self) -> str:
        cpsi_output = self.modem.write("AT+CPSI?")[0]
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

    def log(self, message: str) -> None:
        """
        Logs a message if debug mode is enabled.
        
        :param message: Message to log
        """
        if self.debug:
            print(message)
   
if __name__ == "__main__":
    sms = SIM7600x(debug="true")
    try:
        sms.connect()
        sms.send_sms_to_many(["+14374293006"], "Lab Monitor ⚙️\n1. status\n2. set trigger [value]\n3. set repeat-alerts [on/off]\n4. set alarm [on/off]")
        time.sleep(200)
    finally: 
        sms.close()