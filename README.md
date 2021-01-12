# jlrpy

[![Join the chat at https://gitter.im/jlrpy/community](https://badges.gitter.im/jlrpy/community.svg)](https://gitter.im/jlrpy/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Support the project](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/ardevd/donate)

Python 3 library for interacting with the JLR Remote car API.

## Documentation
The associated API documentation for the JLR InControl API is a good read for anyone wanting to make use of this project. It's currently available [here](https://documenter.getpostman.com/view/6250319/RznBMzqo)

## Installation

Either check out this repository directly or install through pip (for Python3).

`pip install jlrpy`

## Usage
To get started, instantiate a `Connection` object and pass along the email address and password associated with your Jaguar InControl account.

There are two ways to authenticate to InControl. Using the user name and password or with a valid refresh token.

The JLR API requires a device ID to be registered (UUID4 formatted). If you do not specify one when instantiating the `Connection` object it will generate a new one for your automatically. 

```python
import jlrpy
# Authenticate using the username and password
c = jlrpy.Connection('my@email.com', 'password')
v = c.vehicles[0]

# Authenticate using a refresh token (username must still be specified)
c = jlrpy.Connection(email='my@email.com', refresh_token='124c3f21-42ds-2e4d-86f8-221v32392a1d')
```

`Connection.vehicles` will list all vehicles associated with your account.

```python
# Get user information
c.get_user_info()
# Update user information.
p = c.get_user_info()
p['contact']['userPreferences']['unitsOfMeasurement'] = "Km Litre Celsius VolPerDist Wh DistPerkWh"
c.update_user_info(p)
# Refresh access token
c.refresh_tokens()
# Get attributes associated with vehicle
v.get_attributes()
# Get current status of vehicle
v.get_status()
# Get current active services
v.get_services()
# Optionally, you can also specify a status value key
v.get_status("EV_STATE_OF_CHARGE")
# Get subscription packes
v.get_subscription_packages()
# Get trip data (last 1000 trips).
v.get_trips()
# Get data for a single trip (specified with trip id)
v.get_trip(121655021)
# Get vehicle health status
v.get_health_status()
# Get departure timers
v.get_departure_timers()
# Get configured wakeup time
v.get_wakeup_time()
# Honk horn and blink lights
v.honk_blink()
# Get current position of vehicle
v.get_position()
# Start preconditioning at 21.0C
v.preconditioning_start("210")
# Stop preconditioning
v.preconditioning_stop()
# Set vehicle nickname and registration number
v.set_attributes("Name", "reg-number")
# Lock vehicle
v.lock(pin) # pin being the personal master pin
# Unlock vehicle
v.unlock(pin)
# Reset alarm
v.reset_alarm(pin)
# Start charging
v.charging_start()
# Stop charging
v.charging_stop()
# Set max soc at 80% (Requires upcoming OTA update)
v.set_max_soc(80)
# Set max soc for current charging session to 90% (Requires upcoming OTA update)
v.set_one_off_max_soc(90)
# Add single departure timer (index, year, month, day, hour, minute)
v.add_departure_timer(10, 2019, 1, 30, 20, 30)
# Delete a single departure timer index.
v.delete_departure_timer(10)
# Schedule repeated departure timer.
schedule = {"friday":False,"monday":True,"saturday":False,"sunday":False,"thursday":False,"tuesday":True,"wednesday":True}
v.add_repeated_departure_timer(10, 20, 30, schedule)
# Set wakeup timer (epoch millis)
v.set_wakeup_time(1547845200000)
# Cancel wakeup timer
v.delete_wakeup_time()
# Enable service mode (requires personal PIN)
v.enable_service_mode("1234", 1547551847000)
# Enable transport mode (requires personal PIN)
v.enable_transport_mode("1234", 1547551847000)
# Enable privacy mode
v.enable_privacy_mode("1234")
# Disable privacy mode
v.disable_privacy_mode("1234")
# Add charging period with specified index identifier value.
v.add_charging_period(1, schedule, 0, 30, 8, 45)
# Reverse geocode
c.reverse_geocode(59.915475,10.733054)
```

## Examples
The examples directory contains example scripts that put jlrpy to good use. 

### max_min_soc.py
The `max_min_soc.py` script allows you to specify a desired maximum and minimum state of charge for the vehicle. Charging will be stopped once the maximum state of charge is reached and it will be started if the minimum state of charge is reached. 

### charge_offpeak.py
The `charge_offpeak.py` script allows you to specify a desired (off-peak) charging time period and maximum state of charge for the vehicle. Charging will be stopped if the vehicle is charging outside of the specified time period or once the maximum state of charge is reached and it will be started during the specified time period if the state of charge is below the maximum.
