import jlrpy
import threading

def check_soc():
    threading.Timer(60.0, check_soc).start() # Called every minute
    # Get current soc
    current_soc = v.get_status()['vehicleStatus'][2]
    if current_soc >= max_soc:
        # Stop charging
        v.stop_charging()
    
c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

max_soc = 80 # SET MAX SOC LEVEL HERE

print("[*] Connection established. Enforcing max soc")
check_soc()

