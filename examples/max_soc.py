# -*- coding: utf-8 -*-
"""Max SOC script.

This script will check the charging level once every minute
and if the current battery level meets or exceeds the specified
maximum value, the charging will stop if the vehicle is currently charging.
"""

import jlrpy
import threading


max_soc = 80  # SET MAX SOC LEVEL HERE (percentage)


def check_soc():
    """Retrieve vehicle status and stop charging if
    current charging level matches or exceeds specified max level and
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


c = jlrpy.Connection('user@email.com', 'password')
v = c.vehicles[0]

print("[*] Connection established. Enforcing max soc of %d%%" % max_soc)
check_soc()

