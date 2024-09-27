import serial
import time


def send_command(ser, command, valid_resp, timeout=4.0):
        if not ser.isOpen():
            ser.open()
        if ser.timeout != timeout:
            ser.timeout = timeout
            
        # Make sure command is bytes.
        if type(command) is not bytes:
            command = bytes(command, encoding="ascii", errors='replace')
        if type(valid_resp) is not bytes:
            valid_resp = bytes(valid_resp, encoding="ascii", errors="replace")

        # Send the command to the serial port.
        ser.write(command)
        time.sleep(1)
        # Wait until valid_resp is received over the serial port.
        try:
            data = ser.read_until(valid_resp)
        except OSError as err:
            # Read failed, serial port unavailable or error reading.
            data = ""

        # Postprocess data bytes to lines and back again.
        lines = data.splitlines()
        if len(lines) > 0 and lines[0] == command.strip(b'\r\n'):
            lines = lines[1:]       # First line is an echo of our command.
        if len(lines) > 1 and not lines[0] and lines[1] == command.strip(b'\r\n'):
            lines = lines[2:]       # First line blank, second line echo.
        reply = b'\n'.join(lines).decode('latin1')
        return reply
    
    
ser = serial.Serial("/dev/ttyAMA0", 115200, timeout=5)
if not ser.is_open:
    ser.open()
result = send_command(ser, 'AT+CSQ\r', '\nOK')
print(f"Result: {result}")
ser.close()
