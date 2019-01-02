""" Simple Python class to access the JLR Remote Car API
https://github.com/ardevd/jlrpy
"""

from urllib.request import Request, build_opener

import json
import datetime
import calendar
import uuid
import time

class Connection(object):
    """Connection to the JLR Remote Car API"""

    def __init__(self,
                 email='',
                 password='',
                 device_id='', ):
        """Init the connection object

        The email address and password associated with your Jaguar InControl account is required.
        """
        self.email = email

        if device_id:
            self.device_id = device_id
        else:
            self.device_id = str(uuid.uuid4())

        self.oauth = {
            "grant_type": "password",
            "username": email,
            "password": password}
        self.expiration = 0  # force credential refresh

        self.connect()

        self.vehicles = []
        try:
            for v in self.get_vehicles(self.head)['vehicles']:
                self.vehicles.append(Vehicle(v, self))
        except TypeError:
            print("[-] No vehicles associated with this account")

    def get(self, command, url, headers):
        """GET data from API"""
        return self.post(command, url, headers, None)

    def post(self, command, url, headers, data=None):
        """POST data to API"""
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            # Auth expired, reconnect
            self.connect()
        return self.__open("%s/%s" % (url, command), headers=headers, data=data)

    def connect(self):
        print("[*] Connecting...")
        auth = self.__authenticate(data=self.oauth)
        self.__register_auth(auth)
        print("[*] 1/3 authenticated")
        self.__setheader(auth['access_token'], auth['expires_in'])
        self.__register_device(self.head)
        print("[*] 2/3 device id registered")
        self.__login_user(self.head)
        print("[*] 3/3 user logged in, user id retrieved")

    def __open(self, url, headers=None, data=None):
        req = Request(url, headers=headers)
        if data:
            req.data = bytes(json.dumps(data), encoding="utf8")

        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))

    def __register_auth(self, auth):
        self.access_token = auth['access_token']
        now = calendar.timegm(datetime.datetime.now().timetuple())
        self.expiration = now + int(auth['expires_in'])
        self.auth_token = auth['authorization_token']
        self.refresh_token = auth['refresh_token']

    def __setheader(self, access_token, expiration=float('inf')):
        """Set HTTP header fields"""
        self.head = {
            "Authorization": "Bearer %s" % access_token,
            "X-Device-Id": self.device_id,
            "Content-Type": "application/json"}

    def __authenticate(self, data=None):
        """Raw urlopen command to the auth url"""
        url = "https://jlp-ifas.wirelesscar.net/ifas/jlr/tokens"
        auth_headers = {
            "Authorization": "Basic YXM6YXNwYXNz",
            "Content-Type": "application/json",
            "X-Device-Id": self.device_id}

        req = Request(url, headers=auth_headers)
        # Convert data to json
        req.data = bytes(json.dumps(data), encoding="utf8")

        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))

    def __register_device(self, headers=None):
        """Register the device Id"""
        url = "https://jlp-ifop.wirelesscar.net/ifop/jlr/users/%s/clients" % self.email
        data = {
            "access_token": self.access_token,
            "authorization_token": self.auth_token,
            "expires_in": "86400",
            "deviceID": self.device_id
        }

        req = Request(url, headers=headers)
        req.data = bytes(json.dumps(data), encoding="utf8")
        opener = build_opener()
        resp = opener.open(req)
        # TODO: Check for response code

    def __login_user(self, headers=None):
        """Login the user"""
        url = "https://jlp-ifoa.wirelesscar.net/if9/jlr/users?loginName=%s" % self.email
        user_login_header = headers.copy()
        user_login_header["Accept"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json"

        req = Request(url, headers=user_login_header)
        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        """Register user id"""
        userdata = json.loads(resp.read().decode(charset))
        self.user_id = userdata['userId']
        return userdata

    def get_vehicles(self, headers):
        """Get vehicles for user"""
        url = "https://jlp-ifoa.wirelesscar.net/if9/jlr/users/%s/vehicles?primaryOnly=true" % self.user_id

        req = Request(url, headers=headers)
        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')

        return json.loads(resp.read().decode(charset))

    def get_user_info(self):
        """Get user information"""
        return self.get(self.user_id, "https://jlp-ifoa.wirelesscar.net/if9/jlr/users", self.head)


class Vehicle(dict):
    """Vehicle class.

    You can request data or send commands to vehicle. Consult the JLR API documentation for details
    """

    def __init__(self, data, connection):
        """Initialize the vehicle class."""

        super().__init__(data)
        self.connection = connection
        self.vin = data['vin']

    def get_attributes(self):
        """Get vehicle attributes"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.VehicleAttributes-v3+json"
        result = self.get('attributes', headers)
        return result

    def get_status(self):
        """Get vehicle status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.if9.healthstatus-v2+json"
        result = self.get('status', headers)
        return result

    def get_subscription_packages(self):
        """Get vehicle status"""
        result = self.get('subscriptionpackages', self.connection.head)
        return result

    def get(self, command, headers):
        """Utility command to get vehicle data from API"""

        return self.connection.get(command, 'https://jlp-ifoa.wirelesscar.net/if9/jlr/vehicles/%s' % self.vin, headers)
