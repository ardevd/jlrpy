import jlrpy
import threading


max_soc = 80  # SET MAX SOC LEVEL HERE


def check_soc():
    threading.Timer(60.0, check_soc).start()  # Called every minute

    status = v.get_status()['vehicleStatus']
    # Get current soc
    current_soc = int(status[38].get('value'))
    # Get current charging state
    charging_state = status[6]
    if current_soc >= max_soc and charging_state is "CHARGING":
        # Stop charging if we are currently charging
        v.charging_stop()


c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

print("[*] Connection established. Enforcing max soc of %d%%" % max_soc)
check_soc()

