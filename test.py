import serial
import time

def send_at_command(ser, command, expected_response="OK", timeout=1):
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)
    response = ser.read(ser.in_waiting).decode()
    print(f"Command: {command}")
    print(f"Response: {response}")
    return response

def send_sms(phone_number, message):
    ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=1)
    
    # Reset the module to factory defaults
    send_at_command(ser, "AT&F", timeout=5)
    time.sleep(5)  # Wait for the module to reset

    # Check if module is responding
    if "OK" not in send_at_command(ser, "AT"):
        print("Error: Module not responding")
        ser.close()
        return

    # Set character set to GSM
    send_at_command(ser, 'AT+CSCS="GSM"')
    
    # Set text mode
    send_at_command(ser, "AT+CMGF=1")
    
    # Check signal quality
    signal_quality = send_at_command(ser, "AT+CSQ")
    print(f"Signal quality: {signal_quality}")

    # Send message
    send_at_command(ser, f'AT+CMGS="{phone_number}"', ">")
    time.sleep(1)
    ser.write(message.encode() + b'\x1A')  # \x1A is Ctrl+Z
    time.sleep(5)  # Increase timeout for message sending
    
    response = ser.read(ser.in_waiting).decode()
    print(f"Send message response: {response}")
    
    if "+CMGS:" in response:
        print("Message sent successfully")
    else:
        print("Failed to send message")
    
    ser.close()

if __name__ == "__main__":
    recipient_number = "+14374293006"  # Keep the '+' as it was working before
    message_text = "HI I am under the water"
    send_sms(recipient_number, message_text)