# jlrpy

[![Join the chat at https://gitter.im/jlrpy/community](https://badges.gitter.im/jlrpy/community.svg)](https://gitter.im/jlrpy/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Python 3 library for interacting with the JLR Remote car API

## Security notice
The SSL certificates used by JLR are issued by GeoTrust in 2017. Both Apple and Google have distrusted these and others after faliure to comply with industry standards for SSL. If you are running MacOS you will currently get SSL verification errors and subsequently you will be unable to use this script without modifications.

It's unfortunate that JLR relies on distrusted SSL certificates to protect the communication between app and vehicle.

## Usage
To get started, instantiate a `Connection` object and pass along the email address and password associated with your Jaguar InControl account.

The JLR API requires a device ID to be registered (UUID4 formatted). If you do not specify one when instantiating the `Connection` object it will generate a new one for your automatically. 

```python
import jlrpy

con = jlrpy.Connection('my@email.com', 'password')
c.vehicles
```

`Connection.vehicles` will list all vehicles assoiated with your account.

```python
c.vehicles[0].get_attributes()
c.vehicles[0].get_status()
c.vehicles[0].get_subscription_packages()
c.vehicles[0].get_target_temperature()
```
