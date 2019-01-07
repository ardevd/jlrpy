# jlrpy

[![Join the chat at https://gitter.im/jlrpy/community](https://badges.gitter.im/jlrpy/community.svg)](https://gitter.im/jlrpy/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Python 3 library for interacting with the JLR Remote car API. Currently in early development. The associated API documentation for the JLR InControl API is currently in equally early development and is available [here](https://documenter.getpostman.com/view/6250319/RznBMzqo)

## Help Needed
As I currently do not own a vehicle yet the work represented here is the result of static analysis. If anyone with a vehicle is willing to help me reverse the protocol further, please let me known on Gitter. Also, be sure to check out any available pull requests and test out the described functionality there. 

## Security notice
The SSL certificates used by JLR are issued by GeoTrust in 2017. Both Apple and Google have distrusted these and others after faliure to comply with industry standards for SSL. If you are running MacOS you will currently get SSL verification errors and subsequently you will be unable to use this script without modifications. To disable SSL verification you can check out [this guide](http://blog.pengyifan.com/how-to-fix-python-ssl-certificate_verify_failed/).

It's unfortunate that JLR relies on distrusted SSL certificates to protect the communication between app and vehicle. The issue has been reported to JLR.

## Usage
To get started, instantiate a `Connection` object and pass along the email address and password associated with your Jaguar InControl account.

The JLR API requires a device ID to be registered (UUID4 formatted). If you do not specify one when instantiating the `Connection` object it will generate a new one for your automatically. 

```python
import jlrpy

c = jlrpy.Connection('my@email.com', 'password')
c.vehicles
```

`Connection.vehicles` will list all vehicles assosiated with your account.

```python
# Get user information
c.get_user_info()
# Get attributes associated with vehicle
c.vehicles[0].get_attributes()
# Get current status of vehicle
c.vehicles[0].get_status()
# Get subscription packes
c.vehicles[0].get_subscription_packages()
# Get trip data (last 1000 trips).
c.vehicles[0].get_trips()
# Get vehicle health status
c.vehicles[0].get_health_status()
# Get departure timers
c.vehicles[0].get_departure_timers()
# Get configured wakeup time
c.vehicles[0].get_wakeup_time()
# Honk horn and blink lights
c.vehicles[0].honk_blink()
# Get current position of vehicle
c.vehicles[0].get_position()
# Start preconditioning at 21.0C
c.vehicles[0].preconditioning_start("210")
# Stop preconditioning
c.vehicles[0].preconditioning_stop()
```
