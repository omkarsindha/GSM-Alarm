import serial
import time
import threading


class SIM7600x:
    def __init__(self):
        self.port = "/dev/ttyAMA0"
        
        
    def send_at_command(self, ser, command, timeout=1):
        ser.write((command + '\r\n').encode())
        time.sleep(timeout)
        response = ser.read(ser.in_waiting).decode()
        return response

    def send_sms(self, phone_number, message, temp):
        try:
            ser = serial.Serial(self.port, 115200, timeout=5)
            self.send_at_command(ser, "AT")
            self.send_at_command(ser, "AT+CMGF=1")  
            self.send_at_command(ser, 'AT+CSCS="GSM"') 
            self.send_at_command(ser, f'AT+CMGS="{phone_number}"')
            rdble_time = time.strftime("%B %d %Y %H:%M:%S")
            ser.write((f"{message}\n\nTemprature: {temp}°C\nTime: {rdble_time}" + '\x1A').encode())  # Send message and Ctrl+Z
            time.sleep(1)
            
            response = ser.read(ser.in_waiting).decode()
            print(f"Final response: {response}")
            
        except Exception as e:
            print(f"Failed to send message: {e}")
        finally:
            if ser.is_open:
                ser.close()
         
                
    def send_sms_in_thread(self,numbers, message, temp):
        def send_sms():
            for number in numbers:
                self.send_sms(number,message,temp)
        sms_thread = threading.Thread(target=send_sms)
        sms_thread.start()

   

        
        