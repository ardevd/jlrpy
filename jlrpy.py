""" Simple Python class to access the JLR Remote Car API
https://github.com/ardevd/jlrpy
"""

from urllib.request import Request, build_opener

import json
import datetime
import calendar
import uuid


class Connection(object):
    """Connection to the JLR Remote Car API"""

    def __init__(self,
                 email='',
                 password='',
                 access_token='',
                 device_id='',):
        """Init the connection object

        The email address and password associated with your Jaguar InControl account is required.
        """
        self.email = email

        if device_id:
            self.device_id = device_id
        else:
            self.device_id = str(uuid.uuid4())

        if access_token:
            self.__setheader(access_token)
        else:
            self.oauth = {
                "grant_type": "password",
                "username": email,
                "password": password}
            self.expiration = 0  # force credential refresh

        # self.vehicles = [Vehicle(v, self) for v in self.get('
        self.post("hello")

    def post(self, command):
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            auth = self.__authenticate(data=self.oauth)
            self.__register_auth(auth)
            print("[*] 1/3 authenticated")
            self.__setheader(auth['access_token'], auth['expires_in'])
            self.__register_device(self.head)
            print("[*] 2/3 device id registered")
            self.__login_user(self.head)
            print("[*] 3/3 user logged in, user id retrieved")

    def __register_auth(self, auth):
        self.access_token = auth['access_token']
        self.expiration = auth['expires_in']
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

    def __register_device(self, headers={}):
        """Register the device Id"""
        url = "https://jlp-ifop.wirelesscar.net/ifop/jlr/users/%s/clients" % self.email
        data = {
            "access_token": self.access_token,
            "authorization_token": self.auth_token,
            "expires_in": self.expiration,
            "deviceID": self.device_id
        }

        req = Request(url, headers=headers)
        req.data = bytes(json.dumps(data), encoding="utf8")
        opener = build_opener()
        resp = opener.open(req)
        # TODO: Check for response code

    def __login_user(self, headers={}):
        """Login the user"""
        url = "https://jlp-ifoa.wirelesscar.net/if9/jlr/users?loginName=%s" % self.email
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json"

        req = Request(url, headers=headers)
        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        """Register user id"""
        userdata = json.loads(resp.read().decode(charset))
        self.user_id = userdata['userId']
        return userdata



