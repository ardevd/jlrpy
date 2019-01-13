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

    def get_health_status(self):
        """Get vehicle health status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"

        vhs_data = self._authenticate_vhs()

        return self.post('healthstatus', headers, vhs_data)

    def get_departure_timers(self):
        """Get vehicle departure timers"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.DepartureTimerSettings-v1+json"
        return self.get("departuretimers", headers)

    def get_wakeup_time(self):
        """Get configured wakeup time for vehicle"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.VehicleWakeupTime-v2+json"
        return self.get("wakeuptime", headers)

    def get_subscription_packages(self):
        """Get vehicle status"""
        result = self.get('subscriptionpackages', self.connection.head)
        return result

    def get_trips(self):
        """Get the last 1000 trips associated with vehicle"""
        return self.get('trips?count=1000', self.connection.head)

    def get_position(self):
        """Get current vehicle position"""
        return self.get('position', self.connection.head)

    def lock(self, pin):
        """Lock vehicle. Requires personal PIN for authentication"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        rdl_data = self.authenticate_rdl(pin)

        return self.post("lock", headers, rdl_data)

    def unlock(self, pin):
        """Unlock vehicle. Requires personal PIN for authentication"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v2+json"
        rdu_data = self.authenticate_rdu(pin)

        return self.post("unlock", headers, rdu_data)

    def honk_blink(self):
        """Sound the horn and blink lights"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"

        hblf_data = self.authenticate_hblf()
        return self.post("honkBlink", headers, hblf_data)

    def preconditioning_start(self, target_temp):
        """Start pre-conditioning for specified temperature (celsius)"""
        service_parameters = [{"key": "PRECONDITIONING",
                                          "value": "START"},
                                         {"key": "TARGET_TEMPERATURE_CELSIUS",
                                          "value": "%s" % target_temp}]
        return self._preconditioning_control(service_parameters)

    def preconditioning_stop(self):
        """Stop climate preconditioning"""
        service_parameters = [{"key": "PRECONDITIONING",
                               "value": "STOP"}]
        return self._preconditioning_control(service_parameters)

    def climate_prioritize(self, priority):
        """Optimize climate controls for comfort or range"""
        service_parameters = [{"key": "PRIORITY_SETTING",
                               "value": "%s" % priority}]
        return self._preconditioning_control(service_parameters)

    def _preconditioning_control(self, service_parameters):
        """Control the climate preconditioning"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf"

        ecc_data = self.authenticate_ecc()
        ecc_data['serviceParameters'] = service_parameters

        return self.post("preconditioning", headers, ecc_data)

    def charging_stop(self):
        """Stop charging"""
        service_parameters = [{"key": "CHARGE_NOW_SETTING",
                               "value": "FORCE_OFF"}]

        return self._charging_profile_control("serviceParameters", service_parameters)

    def charging_start(self):
        """Start charging"""
        service_parameters = [{"key": "CHARGE_NOW_SETTING",
                               "value": "FORCE_ON"}]

        return self._charging_profile_control("serviceParameters", service_parameters)

    def add_departure_timer(self, index, year, month, day, hour, minute):
        """Add a single departure timer with the specified index"""
        departure_timer_setting = {"timers": [
            {"departureTime": {"hour": hour, "minute": minute},
             "timerIndex": index, "timerTarget":
                 {"singleDay": {"day": day, "month": month, "year": year}},
             "timerType": {"key": "BOTHCHARGEANDPRECONDITION", "value": True}}]}

        return self._charging_profile_control("departureTimerSetting", departure_timer_setting)

    def add_repeated_departure_timer(self, index, schedule, hour, minute):
        """Add repeated departure timer."""
        departure_timer_setting = {"timers": [
            {"departureTime": {"hour": hour, "minute": minute},
             "timerIndex": index, "timerTarget":
                 {"repeatSchedule": schedule},
             "timerType": {"key": "BOTHCHARGEANDPRECONDITION", "value": True}}]}

        return self._charging_profile_control("departureTimerSetting", departure_timer_setting)

    def delete_departure_timer(self, index):
        """Delete a single departure timer associated with the specified index"""
        departure_timer_setting = {"timers": [{"timerIndex": index}]}

        return self._charging_profile_control("departureTimerSetting", departure_timer_setting)

    def _charging_profile_control(self, service_parameter_key, service_parameters):
        """Charging profile API"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf-8"

        cp_data = self.authenticate_cp()
        cp_data[service_parameter_key] = service_parameters

        return self.post("chargeProfile", headers, cp_data)

    def set_wakeup_timer(self, wakeup_time):
        """Set the wakeup timer for the specified time (epoch milliseconds)"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v3+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"

        swu_data = self.authenticate_swu()
        swu_data["serviceCommand"] = "START"
        swu_data["startTime"] = wakeup_time

        return self.post("swu", headers, swu_data)

    def _authenticate_vhs(self):
        """Authenticate to vhs and get token"""
        return self._authenticate_empty_pin_protected_service("VHS")

    def _authenticate_empty_pin_protected_service(self, service_name):
        data = {
            "serviceName": service_name,
            "pin": ""}
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.AuthenticateRequest-v2+json; charset=utf-8"

        return self.post("users/%s/authenticate" % self.connection.user_id, headers, data)

    def authenticate_hblf(self):
        """Authenticate to hblf"""
        return self._authenticate_vin_protected_service("HBLF")

    def authenticate_ecc(self):
        """Authenticate to ecc"""
        return self._authenticate_vin_protected_service("ECC")

    def authenticate_cp(self):
        """Authenticate to cp"""
        return self._authenticate_vin_protected_service("CP")

    def authenticate_swu(self):
        """Authenticate to swu"""
        return self._authenticate_empty_pin_protected_service("SWU")

    def _authenticate_vin_protected_service(self, service_name):
        """Authenticate to specified service and return associated token"""
        data = {
            "serviceName": "%s" % service_name,
            "pin": "%s" % self.vin[-4:]}
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.AuthenticateRequest-v2+json; charset=utf-8"

        return self.post("users/%s/authenticate" % self.connection.user_id, headers, data)

    def authenticate_rdl(self, pin):
        """Authenticate to rdl"""
        return self._authenticate_pin_protected_service(pin, "RDL")

    def authenticate_rdu(self, pin):
        """Authenticate to rdu"""
        return self._authenticate_pin_protected_service(pin, "RDU")

    def _authenticate_pin_protected_service(self, pin, service_name):
        """Authenticate to specified service with the provided PIN"""
        data = {
            "serviceName": "%s" % service_name,
            "pin": "%s" % pin}
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.AuthenticateRequest-v2+json; charset=utf-8"

        return self.post("users/%s/authenticate" % self.connection.user_id, headers, data)

    def post(self, command, headers, data):
        """Utility command to post data to VHS"""
        return self.connection.post(command, 'https://jlp-ifoa.wirelesscar.net/if9/jlr/vehicles/%s' % self.vin,
                                    headers, data)

    def get(self, command, headers):
        """Utility command to get vehicle data from API"""
        return self.connection.get(command, 'https://jlp-ifoa.wirelesscar.net/if9/jlr/vehicles/%s' % self.vin, headers)
