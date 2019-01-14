import jlrpy
import threading

def check_soc():
    threading.Timer(60.0, check_soc).start() # Called every minute
    # Get current soc
    current_soc = int(v.get_status()['vehicleStatus'][38].get('value'))
    if current_soc >= max_soc:
        # Stop charging
        v.charging_stop()
        
c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

max_soc = 80 # SET MAX SOC LEVEL HERE

print("[*] Connection established. Enforcing max soc")
check_soc()

