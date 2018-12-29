# jlrpy

[![Join the chat at https://gitter.im/jlrpy/community](https://badges.gitter.im/jlrpy/community.svg)](https://gitter.im/jlrpy/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Python 3 library for interacting with the JLR Remote car API

## Usage
To get started, instantiate a Connection object and pass along the email address and password associated with your Jaguar InControl account.

The JLR API requires a device ID to be registered (UUID4 formatted). If you do not specify one when instantiating the Connection object it will generate a new one for your automatically. 

```python
import jlrpy

con = jlrpy.Connection('my@email.com', 'password')

c.vehicles
```

`Connection.vehicles` will list all vehicles assoiated with your account.
