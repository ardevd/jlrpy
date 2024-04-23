""" Simple Python class to access the JLR Remote Car API
https://github.com/ardevd/jlrpy
"""


import calendar
import json
import logging
import time
import uuid
from datetime import datetime

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger('jlrpy')


class BaseURLs:
    """Rest Of World Base URLs"""
    IFAS = "https://ifas.prod-row.jlrmotor.com/ifas/jlr"
    IFOP = "https://ifop.prod-row.jlrmotor.com/ifop/jlr"
    IF9 = "https://if9.prod-row.jlrmotor.com/if9/jlr"


class ChinaBaseURLs:
    """China Base URLs"""
    IFAS = "https://ifas.prod-chn.jlrmotor.com/ifas/jlr"
    IFOP = "https://ifop.prod-chn.jlrmotor.com/ifop/jlr"
    IF9 = "https://ifoa.prod-chn.jlrmotor.com/if9/jlr"


TIMEOUT = 15


class Connection:
    """Connection to the JLR Remote Car API"""

    def __init__(self,
                 email='',
                 password='',
                 device_id='',
                 refresh_token='',
                 use_china_servers=False):
        """Init the connection object

        The email address and password associated with your Jaguar InControl account is required.
        A device Id can optionally be specified. If not one will be generated at runtime.
        A refresh token can be supplied for authentication instead of a password
        """
        self.email: str = email
        self.expiration: int = 0  # force credential refresh
        self.access_token: str
        self.auth_token: str
        self.head: dict = {}
        self.refresh_token: str
        self.user_id: str
        self.vehicles: list = []

        if use_china_servers:
            self.base = ChinaBaseURLs
        else:
            self.base = BaseURLs

        if device_id:
            self.device_id = device_id
        else:
            self.device_id = str(uuid.uuid4())

        if refresh_token:
            self.oauth = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token}
        else:
            self.oauth = {
                "grant_type": "password",
                "username": email,
                "password": password}

        self.connect()

        try:
            for vehicle in self.get_vehicles(self.head)['vehicles']:
                self.vehicles.append(Vehicle(vehicle, self))
        except TypeError:
            logger.error("No vehicles associated with this account")

    def validate_token(self):
        """Is token still valid"""
        now = calendar.timegm(datetime.now().timetuple())
        if now > self.expiration:
            # Auth expired, reconnect
            self.connect()

    def get(self, command, url, headers):
        """GET data from API"""
        self.validate_token()
        if headers['Authorization']:
            headers['Authorization'] = self.head['Authorization']
        return self._request(f"{url}/{command}", headers=headers, method="GET")

    def post(self, command, url, headers, data=None):
        """POST data to API"""
        self.validate_token()
        if headers['Authorization']:
            headers['Authorization'] = self.head['Authorization']
        return self._request(f"{url}/{command}", headers=headers, data=data, method="POST")

    def delete(self, command, url, headers):
        """DELETE data from api"""
        self.validate_token()
        if headers['Authorization']:
            headers['Authorization'] = self.head['Authorization']
        if headers["Accept"]:
            del headers["Accept"]
        return self._request(url=f"{url}/{command}", headers=headers, method="DELETE")

    def connect(self):
        """Connect to JLR API"""
        logger.info("Connecting...")
        auth = self._authenticate(data=self.oauth)
        self._register_auth(auth)
        self._set_header(auth['access_token'])
        logger.info("[+] authenticated")
        self._register_device_and_log_in()

    def _register_device_and_log_in(self):
        self._register_device(self.head)
        logger.info("1/2 device id registered")
        self._login_user(self.head)
        logger.info("2/2 user logged in, user id retrieved")

    def _request(self, url, headers=None, data=None, method="GET"):
        ret = requests.request(method=method, url=url, headers=headers, json=data, timeout=TIMEOUT)
        if ret.text:
            try:
                return json.loads(ret.text)
            except json.JSONDecodeError:
                return None
        return None

    def _register_auth(self, auth):
        self.access_token = auth['access_token']
        now = calendar.timegm(datetime.now().timetuple())
        self.expiration = now + int(auth['expires_in'])
        self.auth_token = auth['authorization_token']
        self.refresh_token = auth['refresh_token']

    def _set_header(self, access_token):
        """Set HTTP header fields"""
        self.head = {
            "Authorization": f"Bearer {access_token}",
            "X-Device-Id": self.device_id,
            "x-telematicsprogramtype": "jlrpy",
            "x-App-Id": "ICR_JAGUAR_ANDROID",
            "x-App-Secret": "7bf6f544-1926-4714-8066-ceceb40d538d",
            "Content-Type": "application/json"}

    def _authenticate(self, data=None):
        """Raw urlopen command to the auth url"""
        url = f"{self.base.IFAS}/tokens/tokensSSO"
        auth_headers = {
            "Authorization": "Basic YXM6YXNwYXNz",
            "Content-Type": "application/json",
            "user-agent": "jlrpy"}

        return self._request(url, auth_headers, data, "POST")

    def _register_device(self, headers=None):
        """Register the device Id"""
        url = f"{self.base.IFOP}/users/{self.email}/clients"
        data = {
            "access_token": self.access_token,
            "authorization_token": self.auth_token,
            "expires_in": "86400",
            "deviceID": self.device_id
        }

        return self._request(url, headers, data, "POST")

    def _login_user(self, headers=None):
        """Login the user"""
        url = f"{self.base.IF9}/users?loginName={self.email}"
        user_login_header = headers.copy()
        user_login_header["Accept"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json"

        user_data = self._request(url, user_login_header)
        self.user_id = user_data['userId']
        return user_data

    def refresh_tokens(self):
        """Refresh tokens."""
        self.oauth = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token}

        auth = self._authenticate(self.oauth)
        self._register_auth(auth)
        self._set_header(auth['access_token'])
        logger.info("[+] Tokens refreshed")
        self._register_device_and_log_in()

    def get_vehicles(self, headers):
        """Get vehicles for user"""
        url = f"{self.base.IF9}/users/{self.user_id}/vehicles?primaryOnly=true"
        return self._request(url, headers)

    def get_user_info(self):
        """Get user information"""
        headers = self.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json"
        headers["Content-Type"] = "application/json"
        return self.get("", f"{self.base.IF9}/users?loginName={self.email}", self.head)

    def update_user_info(self, user_info_data):
        """Update user information"""
        headers = self.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.User-v3+json; charset=utf-8"
        return self.post(self.user_id, f"{self.base.IF9}/users", headers, user_info_data)

    def reverse_geocode(self, lat, lon):
        """Get geocode information"""
        headers = self.head.copy()
        headers["Accept"] = "application/json"
        return self.get("en", f"{self.base.IF9}/geocode/reverse/{lat}/{lon}", headers)


class Vehicle(dict):
    """Vehicle class.

    You can request data or send commands to vehicle. Consult the JLR API documentation for details
    """

    def __init__(self, data, connection):
        """Initialize the vehicle class."""

        super().__init__(data)
        self.connection = connection
        self.vin = data['vin']

    def get_contact_info(self, mcc):
        """ Get contact info for the specified mobile country code"""
        headers = self.connection.head.copy()
        return self.get(f"contactinfo/{mcc}", headers)

    def get_attributes(self):
        """Get vehicle attributes"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.VehicleAttributes-v8+json"
        return self.get('attributes', headers)

    def get_status(self, key=None):
        """Get vehicle status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.if9.healthstatus-v4+json"
        result = self.get('status?includeInactive=true', headers)

        if key:
            core_status = result['vehicleStatus']['coreStatus']
            ev_status = result['vehicleStatus']['evStatus']
            core_status = core_status + ev_status
            return {d['key']: d['value'] for d in core_status}[key]

        return result

    def get_health_status(self):
        """Get vehicle health status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"  # noqa: E501, pylint: disable=line-too-long

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
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.SubscriptionPackages-v2+json"
        result = self.get('subscriptionpackages', headers)
        return result

    def get_trips(self, count=1000, start=None, stop=None):
        """Get the last 1000 trips associated with vehicle. Start/Stop strings in ISO 8601 format."""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.ngtp.org.triplist-v2+json"
        path = 'trips?'
        if start != None:
            s = datetime.fromisoformat(start).isoformat(timespec='minutes')
            utc_tz = datetime.fromisoformat(s[:16]+'+0000').tzinfo
            s = datetime.fromisoformat(start).astimezone(utc_tz).isoformat(timespec='seconds')
            s = s[:19]+'+0000'
            path += 'startDate='+requests.utils.quote(s)+'&'
        if stop != None:
            s = datetime.fromisoformat(stop).isoformat(timespec='minutes')
            utc_tz = datetime.fromisoformat(s[:16]+'+0000').tzinfo
            s = datetime.fromisoformat(stop).astimezone(utc_tz).isoformat(timespec='seconds')
            s = s[:19]+'+0000'
            path += 'stopDate='+requests.utils.quote(s)+'&'
        path += f"count={count}"
        return self.get(path, headers)

    def get_guardian_mode_alarms(self):
        """Get Guardian Mode Alarms"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianStatus-v1+json"
        headers["Accept-Encoding"] = "gzip,deflate"
        return self.get('gm/alarms', headers)

    def get_guardian_mode_alerts(self):
        """Get Guardian Mode Alerts"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/wirelesscar.GuardianAlert-v1+json"
        headers["Accept-Encoding"] = "gzip,deflate"
        return self.get('gm/alerts', headers)

    def get_guardian_mode_status(self):
        """Get Guardian Mode Status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianStatus-v1+json"
        return self.get('gm/status', headers)

    def get_guardian_mode_settings_user(self):
        """Get Guardian Mode User Settings"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianUserSettings-v1+json"
        return self.get('gm/settings/user', headers)

    def get_guardian_mode_settings_system(self):
        """Get Guardian Mode System Settings"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianSystemSettings-v1+json"
        return self.get('gm/settings/system', headers)

    def get_trip(self, trip_id, section=1):
        """Get info on a specific trip"""
        return self.get(f"trips/{trip_id}/route?pageSize=1000&page={section}", self.connection.head)

    def get_position(self):
        """Get current vehicle position"""
        return self.get('position', self.connection.head)

    def get_service_status(self, service_id):
        """Get service status"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        return self.get(f"services/{service_id}", headers)

    def get_services(self):
        """Get active services"""
        headers = self.connection.head.copy()
        return self.get("services", headers)

    def get_rcc_target_value(self):
        """Get Remote Climate Target Value"""
        headers = self.connection.head.copy()
        try:
            return self.get('settings/ClimateControlRccTargetTemp', headers)
        except HTTPError:
            return None

    def set_attributes(self, nickname, registration_number):
        """Set vehicle nickname and registration number"""
        attributes_data = {"nickname": nickname,
                           "registrationNumber": registration_number}
        return self.post("attributes", self.connection.head, attributes_data)

    def lock(self, pin):
        """Lock vehicle. Requires personal PIN for authentication"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        rdl_data = self.authenticate_rdl(pin)

        return self.post("lock", headers, rdl_data)

    def unlock(self, pin):
        """Unlock vehicle. Requires personal PIN for authentication"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        rdu_data = self.authenticate_rdu(pin)

        return self.post("unlock", headers, rdu_data)

    def reset_alarm(self, pin):
        """Reset vehicle alarm"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"  # noqa: E501, pylint: disable=line-too-long
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        aloff_data = self.authenticate_aloff(pin)

        return self.post("unlock", headers, aloff_data)

    def honk_blink(self):
        """Sound the horn and blink lights"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v4+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"  # noqa: E501, pylint: disable=line-too-long

        hblf_data = self.authenticate_hblf()
        return self.post("honkBlink", headers, hblf_data)

    def remote_engine_start(self, pin, target_value):
        """Start Remote Engine preconditioning"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        self.set_rcc_target_value(pin, target_value)
        reon_data = self.authenticate_reon(pin)

        return self.post("engineOn", headers, reon_data)

    def remote_engine_stop(self, pin):
        """Stop Remote Engine preconditioning"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        reoff_data = self.authenticate_reoff(pin)

        return self.post("engineOff", headers, reoff_data)

    def set_rcc_target_value(self, pin, target_value):
        """Set Remote Climate Target Value (value between 31-57, 31 is LO 57 is HOT)"""
        headers = self.connection.head.copy()
        self.enable_provisioning_mode(pin)
        service_parameters = {
            "key": "ClimateControlRccTargetTemp",
            "value": str(target_value),
            "applied": 1
        }
        self.post("settings", headers, service_parameters)

    def get_waua_status(self):
        """Get WAUA status."""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/wirelesscar.WauaStatus-v1+json"
        return self.get("waua/status", headers)

    def preconditioning_start(self, target_temp):
        """Start pre-conditioning for specified temperature (celsius)"""
        service_parameters = [
            {"key": "PRECONDITIONING", "value": "START"},
            {"key": "TARGET_TEMPERATURE_CELSIUS", "value": str(target_temp)}
        ]
        return self._preconditioning_control(service_parameters)

    def preconditioning_stop(self):
        """Stop climate preconditioning"""
        service_parameters = [{"key": "PRECONDITIONING",
                               "value": "STOP"}]
        return self._preconditioning_control(service_parameters)

    def climate_prioritize(self, priority):
        """Optimize climate controls for comfort or range"""
        service_parameters = [{"key": "PRIORITY_SETTING", "value": priority}]
        return self._preconditioning_control(service_parameters)

    def _preconditioning_control(self, service_parameters):
        """Control the climate preconditioning"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf-8"

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

    def set_max_soc(self, max_charge_level):
        """Set max state of charge in percentage"""
        service_parameters = [{"key": "SET_PERMANENT_MAX_SOC",
                               "value": max_charge_level}]

        return self._charging_profile_control("serviceParameters", service_parameters)

    def set_one_off_max_soc(self, max_charge_level):
        """Set one off max state of charge in percentage"""
        service_parameters = [{"key": "SET_ONE_OFF_MAX_SOC",
                               "value": max_charge_level}]

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

    def add_charging_period(self, index, schedule, hour_from, minute_from, hour_to, minute_to):
        """Add charging period"""
        tariff_settings = {"tariffs": [
            {"tariffIndex": index, "tariffDefinition": {"enabled": True,
                                                        "repeatSchedule": schedule,
                                                        "tariffZone": [
                                                            {"zoneName": "TARIFF_ZONE_A",
                                                             "bandType": "PEAK",
                                                             "endTime": {
                                                                 "hour": hour_from,
                                                                 "minute": minute_from}},
                                                            {"zoneName": "TARIFF_ZONE_B",
                                                             "bandType": "OFFPEAK",
                                                             "endTime": {"hour": hour_to,
                                                                         "minute": minute_to}},
                                                            {"zoneName": "TARIFF_ZONE_C",
                                                             "bandType": "PEAK",
                                                             "endTime": {"hour": 0,
                                                                         "minute": 0}}]}}]}

        return self._charging_profile_control("tariffSettings", tariff_settings)

    def _charging_profile_control(self, service_parameter_key, service_parameters):
        """Charging profile API"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v5+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.PhevService-v1+json; charset=utf-8"

        cp_data = self.authenticate_cp()
        cp_data[service_parameter_key] = service_parameters

        return self.post("chargeProfile", headers, cp_data)

    def set_wakeup_time(self, wakeup_time):
        """Set the wakeup time for the specified time (epoch milliseconds)"""
        swu_data = self.authenticate_swu()
        swu_data["serviceCommand"] = "START"
        swu_data["startTime"] = wakeup_time
        return self._swu(swu_data)

    def delete_wakeup_time(self):
        """Stop the wakeup time"""
        swu_data = self.authenticate_swu()
        swu_data["serviceCommand"] = "END"
        return self._swu(swu_data)

    def _swu(self, swu_data):
        """Set the wakeup time for the specified time (epoch milliseconds)"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.ServiceStatus-v3+json"
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json; charset=utf-8"  # noqa: E501, pylint: disable=line-too-long
        return self.post("swu", headers, swu_data)

    def enable_provisioning_mode(self, pin):
        """Enable provisioning mode """
        self._prov_command(pin, None, "provisioning")

    def enable_service_mode(self, pin, expiration_time):
        """Enable service mode. Will disable at the specified time (epoch millis)"""
        return self._prov_command(pin, expiration_time, "protectionStrategy_serviceMode")

    def disable_service_mode(self, pin):
        """Disable service mode."""
        exp = int(time.time() * 1000)
        return self._prov_command(pin, exp, "protectionStrategy_serviceMode")

    def enable_guardian_mode(self, pin, expiration_time):
        """Enable Guardian Mode until the specified time (epoch millis)"""
        return self._gm_command(pin, expiration_time, "ACTIVATE")

    def disable_guardian_mode(self, pin):
        """Disable Guardian Mode"""
        return self._gm_command(pin, 0, "DEACTIVATE")

    def enable_transport_mode(self, pin, expiration_time):
        """Enable transport mode. Will be disabled at the specified time (epoch millis)"""
        return self._prov_command(pin, expiration_time, "protectionStrategy_transportMode")

    def disable_transport_mode(self, pin):
        """Disable transport mode"""
        exp = int(time.time() * 1000)
        return self._prov_command(pin, exp, "protectionStrategy_transportMode")

    def enable_privacy_mode(self, pin):
        """Enable privacy mode. Will disable journey logging"""
        return self._prov_command(pin, None, "privacySwitch_on")

    def disable_privacy_mode(self, pin):
        """Disable privacy mode. Will enable journey logging"""
        return self._prov_command(pin, None, "privacySwitch_off")

    def _prov_command(self, pin, expiration_time, mode):
        """Send prov endpoint commands. Used for service/transport/privacy mode"""
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.StartServiceConfiguration-v3+json"
        prov_data = self.authenticate_prov(pin)

        prov_data["serviceCommand"] = mode
        prov_data["startTime"] = None
        prov_data["endTime"] = expiration_time

        return self.post("prov", headers, prov_data)

    def _gm_command(self, pin, expiration_time, action):
        """Send GM toggle command"""
        headers = self.connection.head.copy()
        headers["Accept"] = "application/vnd.wirelesscar.ngtp.if9.GuardianAlarmList-v1+json"
        gm_data = self.authenticate_gm(pin)
        if action == "ACTIVATE":
            gm_data["endTime"] = expiration_time
            gm_data["status"] = "ACTIVE"
            return self.post("gm/alarms", headers, gm_data)
        if action == "DEACTIVATE":
            headers["X-servicetoken"] = gm_data.get("token")
            return self.delete("gm/alarms/INSTANT", headers)

    def _authenticate_vhs(self):
        """Authenticate to vhs and get token"""
        return self._authenticate_empty_pin_protected_service("VHS")

    def _authenticate_empty_pin_protected_service(self, service_name):
        return self._authenticate_service("", service_name)

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
        return self._authenticate_service(self.vin[-4:], service_name)

    def authenticate_rdl(self, pin):
        """Authenticate to rdl"""
        return self._authenticate_service(pin, "RDL")

    def authenticate_rdu(self, pin):
        """Authenticate to rdu"""
        return self._authenticate_service(pin, "RDU")

    def authenticate_aloff(self, pin):
        """Authenticate to aloff"""
        return self._authenticate_service(pin, "ALOFF")

    def authenticate_reon(self, pin):
        """Authenticate to reon"""
        return self._authenticate_service(pin, "REON")

    def authenticate_reoff(self, pin):
        """Authenticate to reoff"""
        return self._authenticate_service(pin, "REOFF")

    def authenticate_prov(self, pin):
        """Authenticate to PROV service"""
        return self._authenticate_service(pin, "PROV")

    def authenticate_gm(self, pin):
        """Authenticate to GM service"""
        return self._authenticate_service(pin, "GM")

    def _authenticate_service(self, pin, service_name):
        """Authenticate to specified service with the provided PIN"""
        data = {
            "serviceName": service_name,
            "pin": str(pin)
        }
        headers = self.connection.head.copy()
        headers["Content-Type"] = "application/vnd.wirelesscar.ngtp.if9.AuthenticateRequest-v2+json; charset=utf-8"
        return self.post(f"users/{self.connection.user_id}/authenticate", headers, data)

    def get(self, command, headers):
        """Utility command to get vehicle data from API"""
        return self.connection.get(command, f"{self.connection.base.IF9}/vehicles/{self.vin}", headers)

    def post(self, command, headers, data):
        """Utility command to post data to VHS"""
        return self.connection.post(command, f"{self.connection.base.IF9}/vehicles/{self.vin}", headers, data)

    def delete(self, command, headers):
        """Utility command to delete active service entry"""
        return self.connection.delete(command, f"{self.connection.base.IF9}/vehicles/{self.vin}", headers)
