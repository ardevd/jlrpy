# jlrpy

[![Join the chat at https://gitter.im/jlrpy/community](https://badges.gitter.im/jlrpy/community.svg)](https://gitter.im/jlrpy/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Python 3 library for interacting with the JLR Remote car API.

## Documentation
The associated API documentation for the JLR InControl API is a good read for anyone wanting to make use of this project. It's currently available [here](https://documenter.getpostman.com/view/6250319/RznBMzqo)

## Help Needed
As I currently do not own a vehicle yet the work represented here is the result of static analysis. If anyone with a vehicle is willing to help me reverse the protocol further, please let me know on Gitter. Also, be sure to check out any available pull requests and test out the described functionality there. 

## Security notice
The SSL certificates used by JLR are issued by GeoTrust in 2017. Both Apple and Google have distrusted these and others after faliure to comply with industry standards for SSL. If you are running MacOS you will currently get SSL verification errors and subsequently you will be unable to use this script without modifications. To disable SSL verification you can check out [this guide](http://blog.pengyifan.com/how-to-fix-python-ssl-certificate_verify_failed/).

## Installation

Either check out this repository directly or install through pip (for Python3).

`pip install jlrpy`

## Usage
To get started, instantiate a `Connection` object and pass along the email address and password associated with your Jaguar InControl account.

The JLR API requires a device ID to be registered (UUID4 formatted). If you do not specify one when instantiating the `Connection` object it will generate a new one for your automatically. 

```python
import jlrpy

c = jlrpy.Connection('my@email.com', 'password')
v = c.vehicles[0]
```

`Connection.vehicles` will list all vehicles assosiated with your account.

```python
# Get user information
c.get_user_info()
# Update user information.
p = c.get_user_info()
p['contact']['userPreferences']['unitsOfMeasurement'] = "Km Litre Celsius VolPerDist Wh DistPerkWh"
c.update_user_info(p)
# Get attributes associated with vehicle
v.get_attributes()
# Get current status of vehicle
v.get_status()
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
v.lock()
# Unlock vehicle
v.unlock()
# Reset alarm
v.reset_alarm("1234") # 1234 being the personal PIN
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
schedule = {"friday":false,"monday":true,"saturday":false,"sunday":false,"thursday":false,"tuesday":true,"wednesday":true}
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
