# -*- coding: utf-8 -*-
"""Charge Off-Peak script.

This script will check the charging level once every minute
if the vehicle is at home (100 meters or less from the location
specified in the config file) and if the current battery level 
meets or exceeds the specified maximum value, the charging will
stop if the vehicle is currently charging.

If the vehicle is charging during off-peak hours, the charging will stop.

"""

import jlrpy
import threading
import datetime
import math
from datetime import date
import os
import configparser


# login info (email and password) are read from $HOME/.jlrpy.cfg
# which contains a single line with email and password separated by ':'
# email@example.com:PassW0rd
# passwords containing a ':' are not allowed

logger = jlrpy.logger

def distance(origin, destination):
    """
    From https://stackoverflow.com/questions/19412462

    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c
    return d

def check_soc():
    """Retrieve vehicle status and stop or start charging if
    current charging level matches or exceeds specified max level and
    the vehicle is currently charging.
    """
    threading.Timer(60.0, check_soc).start()  # Called every minute

    p = v.get_position()
    position = (p['position']['latitude'], p['position']['longitude'])
    d = int(1000*distance(home,position))
    if (d > 100):
        logger.info("car is "+str(d)+"m from home")
        return

    t = datetime.datetime.now()
    # offpeak: M-F (0-4) 0:00- 7:00, 23:00-23:59
    #          S-S (5-6) 0:00-15:00, 19:00-23:59 
    today = date.weekday(t)
    offpeak = ( (t.hour <  peak[today][0] or t.hour >= peak[today][1]))

    # getting health status forces a status update
    healthstatus = v.get_health_status()
    # get the vehicle status 
    vehicleStatus = v.get_status()['vehicleStatus']
    #we have a list of keys and values - we need to convert to a dict to make it more usable
    status = { d['key'] : d['value'] for d in vehicleStatus }

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

config = configparser.ConfigParser()
configfile = os.environ['HOME']+"/.jlrpy.ini"
config.read(configfile)
username = config['jlrpy']['email']
password = config['jlrpy']['password']
home = (float(config['jlrpy']['home_latitude']), float(config['jlrpy']['home_longitude']))
max_soc = int(config['jlrpy']['max_soc'])

peak = [ [int(config['jlrpy']['peak_start_mon']),int(config['jlrpy']['peak_end_mon'])],
         [int(config['jlrpy']['peak_start_tue']),int(config['jlrpy']['peak_end_tue'])],
         [int(config['jlrpy']['peak_start_wed']),int(config['jlrpy']['peak_end_wed'])],
         [int(config['jlrpy']['peak_start_thu']),int(config['jlrpy']['peak_end_thu'])],
         [int(config['jlrpy']['peak_start_fri']),int(config['jlrpy']['peak_end_fri'])],
         [int(config['jlrpy']['peak_start_sat']),int(config['jlrpy']['peak_end_sat'])],
         [int(config['jlrpy']['peak_start_sun']),int(config['jlrpy']['peak_end_sun'])]]

c = jlrpy.Connection(username, password)
v = c.vehicles[0]

logger.info("[*] Enforcing offpeak charging to max soc of %d%%" % max_soc)
check_soc()
