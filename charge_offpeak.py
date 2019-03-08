# -*- coding: utf-8 -*-
"""Max SOC script.

This script will check the charging level once every minute
and if the current battery level meets or exceeds the specified
maximum value, the charging will stop if the vehicle is currently charging.

If the vehicle is charging during off-peak hours, the charging will stop.

Todo: figure out whether the car is plugged in at home or somewhere else.

"""

import jlrpy
import threading
import datetime
from datetime import date
import os

max_soc = 80  # SET MAX SOC LEVEL HERE (percentage)

# login info (email and password) are read from $HOME/.jlrpy.cfg
# which contains a single line with email and password separated by ':'
# email@example.com:PassW0rd
# passwords containing a ':' are not allowed
passwordfile = os.environ['HOME']+"/.jlrpy.cfg"

logger = jlrpy.logger

def check_soc():
    """Retrieve vehicle status and stop or start charging if
    current charging level matches or exceeds specified max/min level and
    the vehicle is currently charging.
    """
    threading.Timer(60.0, check_soc).start()  # Called every minute

    t = datetime.datetime.now()
    # offpeak: M-F (0-4) 0:00- 7:00, 23:00-23:59
    #          S-S (5-6) 0:00-15:00, 19:00-23:59 
    offpeak = ((date.weekday(t) <  5 and (t.hour <  7 or t.hour >= 23)) or
               (date.weekday(t) >= 5 and (t.hour < 15 or t.hour >= 19)))

    # getting health status forces a status update
    healthstatus = v.get_health_status()
    status = { d['key'] : d['value'] for d in v.get_status()['vehicleStatus'] }

    current_soc = int(status['EV_STATE_OF_CHARGE'])
    charging_status = status['EV_CHARGING_STATUS']
    logger.info("current SoC is "+str(current_soc)+"%"+", offpeak is "+str(offpeak))

    if status['EV_CHARGING_METHOD']  == "WIRED":
        logger.info("car is plugged in")
        logger.info("charging status is "+charging_status)
        if offpeak:
            # allow for SoC to drop a little to avoid restarting too often
            if current_soc < max_soc-1 and charging_status == "PAUSED":
                logger.info("sending start charging request")
                v.charging_start()
            elif current_soc >= max_soc and charging_status == "CHARGING":
                # Stop charging if max SoC is reached
                logger.info("sending stop charging request")
                v.charging_stop()
        elif charging_status == "CHARGING":
            # Stop charging if we are charging during peak
            logger.info("sending stop charging request")
            v.charging_stop()
    else:
        logger.info("car is not plugged in")

file = open(passwordfile, "r")
line = file.readline()
s = line.strip().split(":")
username = s[0]
password = s[1]

c = jlrpy.Connection(username, password)
v = c.vehicles[0]

logger.info("[*] Enforcing offpeak charging to max soc of %d%%" % max_soc)
check_soc()
