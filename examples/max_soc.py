import jlrpy
import threading


max_soc = 80  # SET MAX SOC LEVEL HERE
max_soc_reached = False


def check_soc():
    global max_soc_reached
    threading.Timer(60.0, check_soc).start() # Called every minute
    # Get current soc
    current_soc = int(v.get_status()['vehicleStatus'][38].get('value'))
    if current_soc >= max_soc and not max_soc_reached:
        # Stop charging
        v.charging_stop()
        max_soc_reached = True
    else:
        max_soc_reached = False


c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

print("[*] Connection established. Enforcing max soc")
check_soc()

