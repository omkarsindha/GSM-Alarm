import pijuice
import threading
import time

class UPS():
    def __init__(self):
        try:
            self.ups = pijuice.PiJuice(1, 0x14)
        except Exception as e:
            print(f"Error initializing PiJuice: {e}")
            self.ups = None

    def get_power_source(self) -> str:
        """
        Returns '120V-AC' if connected to active power, 'UPS' if running on
        battery or None in case of any error 
        """
        if not self.ups:
            print("Error: PiJuice not initialized")
            return None
        
        try:
            status = self.ups.status.GetStatus()
            if status['error'] == 'NO_ERROR':
                data = status.get('data', {})
                if data.get('powerInput') == 'NOT_PRESENT' and data.get('powerInput5vIo') == 'NOT_PRESENT':
                    return "UPS"
                else:
                    return "120V-AC"
            else:
                print(f"Error: {status['error']}")
                return None
        except Exception as e:
            print(f"Error while checking power supply status: {e}")
            return None

    def get_battery_level(self) -> int:
        """Returns the battery percentage of the UPS, returns None in case of error"""
        if not self.ups:
            print("Error: PiJuice not initialized")
            return None
        
        try:
            status = self.ups.status.GetChargeLevel()
            if status['error'] == 'NO_ERROR':
                return status['data']
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

if __name__ == "__main__":
    ups = UPS()
    for _ in range(5):
        print(ups.get_status())
        print(ups.get_battery_level())
        time.sleep(1)