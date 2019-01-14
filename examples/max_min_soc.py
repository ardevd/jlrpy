# -*- coding: utf-8 -*-
"""Max SOC script.

This script will check the charging level once every minute
and if the current battery level meets or exceeds the specified
maximum value, the charging will stop if the vehicle is currently charging.

You can also specify a minimum charging level and ensure charging is started
if the battery level drops below the specified minimum state of charge.
"""

import jlrpy
import threading


max_soc = 80  # SET MAX SOC LEVEL HERE (percentage)
min_soc = 20  # SET MIN SOC LEVEL HERE


def check_soc():
    """Retrieve vehicle status and stop or start charging if
    current charging level matches or exceeds specified max/min level and
    the vehicle is currently charging.
    """
    threading.Timer(60.0, check_soc).start()  # Called every minute

    status = v.get_status()['vehicleStatus']
    # Get current soc
    current_soc = int(status[38].get('value'))
    # Get current charging state
    charging_state = status[6]
    if current_soc >= max_soc and charging_state is "CHARGING":
        # Stop charging if we are currently charging
        v.charging_stop()
    elif current_soc < min_soc and charging_state is "NOT CHARGING":
        # Start charging
        v.charging_start()


c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

print("[*] Enforcing max soc of %d%%" % max_soc)
print("[*] Enforcing min soc of %d%%" % min_soc)
check_soc()

