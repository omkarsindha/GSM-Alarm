from pijuice import PiJuice
import threading
import time 

class UPS():
    def __init__(self):
      self.ups = PiJuice(1, 0x14)
                 
    def get_status(self) -> str:
        """Returns '120V-AC' or 'UPS' string depending on the state of the power supply to pi"""
        status = self.ups.status.GetStatus().get('data', None)
        if status:
            if status['powerInput'] == 'NOT_PRESENT' and status['powerInput5vIo'] == 'NOT_PRESENT':
                return "UPS"
            else:
                return "120V-AC"
        else:
            return None
        
    def get_battery_level(self) -> int:
        """Returns the battery percentage of the UPS"""
        status = self.ups.status.GetChargeLevel()  
        if status['error'] == 'NO_ERROR':
            return status['data']  
        else:
            return f"Error: {status['error']}"
                       
if __name__ == "__main__":
    ups = UPS()
    for _ in range(5):
        print(ups.get_status())
        print(type(ups.get_battery_level()))
        time.sleep(1)
    print(ups.get_battery_level())
        
        
# class UPS(threading.Thread):
#     def __init__(self, debug=False, **kwargs):
#         super(UPS, self).__init__(name="UPS", **kwargs)
#         self._power = 'GRID'
#         self.ups = PiJuice(1, 0x14)
#         self.debug = debug
#         self.end_event = threading.Event()
#         self.lock = threading.Lock()
                 
#     def get_power(self):
#         with self.lock:
#             return self._power
        
#     def ups_loop(self):
#         while self.end_event.is_set() is False:
#             status = self.ups.status.GetStatus()['data']
#             if status['powerInput'] == 'NOT_PRESENT' and status['powerInput5vIo'] == 'NOT_PRESENT':
#                 with self.lock:
#                     self._power = "UPS"
#             else:
#                 with self.lock:
#                     self._power = "GRID"
#             time.sleep(1)
            
#     def run(self):
#         try:
#             self.ups_loop()
#         except Exception as err:
#             error = str(err) if str(err) else str(err.__class__.__name__)
#             self.log("Thread failed: %s" % error)
#             self.error = "Unhandled exception: %s" % error
            
#     def stop(self, block=False):
#         """Signal the thread to end. Block only if block=True."""
#         self.end_event.set()
#         if block is True:
#             self.join() 
            
#     def log(self, message):
#         if self.debug:
#             print(message)
            
            
# if __name__ == "__main__":
#     ups_thread = UPS(debug=True)
#     ups_thread.start()
#     time.sleep(5)
#     ups_thread.stop()
#     print(f"{ups_thread.get_power()} hi")
    
        
        