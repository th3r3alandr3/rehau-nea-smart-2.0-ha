from homeassistant.core import HomeAssistant
from .types.installation import Installation, Zone
from .MqttClient import MqttClient
from .utils.helpers import replace_keys, EnergyLevels, OperationModes


class Controller:
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        self.mqtt_client = MqttClient(hass, username=email, password=password)
        self.hass = hass

    async def connect(self):
        await self.mqtt_client.auth_user()

    async def disconnect(self):
        await self.mqtt_client.disconnect()

    def is_authenticated(self):
        return self.mqtt_client.is_authenticated()

    def get_installations(self) -> list[Installation]:
        installations = self.mqtt_client.get_installations()
        if installations is None:
            return None
        return [Installation(**installation) for installation in installations]

    def get_installations_as_dict(self) -> list[dict]:
        return self.mqtt_client.get_installations()

    def get_zones(self) -> list[Zone]:
        zones = []
        for installation in self.get_installations():
            for group in installation.groups:
                for zone in group.zones:
                    zones.append(zone)
        return zones

    def get_zone(self, zone_number: int) -> Zone:
        for zone in self.get_zones():
            if zone.number == zone_number:
                return zone
        raise Exception("No zone found for zone " + str(zone_number))

    def get_installation_unique_by_zone(self, zone_number: int):
        installations = self.get_installations_as_dict()
        for installation in installations:
            for group in installation["groups"]:
                for zone in group["zones"]:
                    if zone["number"] == zone_number:
                        return installation["unique"]
        raise Exception("No zone found for zone " + str(zone_number))

    def get_zone_value_by_key(self, key: str, zone_number: int):
        installations = self.get_installations_as_dict()
        for installation in installations:
            for group in installation["groups"]:
                for zone in group["zones"]:
                    if zone["number"] == zone_number:
                        if len(zone["channels"]) > 1 or key != "_id":
                            values = []
                            for channel in zone["channels"]:
                                if key in channel:
                                    values.append(channel[key])
                            if len(values) == 0:
                                raise Exception("No value found for key " + key + " in zone " + str(zone_number))
                            return sum(values) / len(values)
                        else:
                            raise Exception(
                                "Multiple channels found for zone " + str(zone_number) + " cannot return _id")
        raise Exception("No zone found for zone " + str(zone_number))

    def get_temperature(self, zone: int, unit="C"):
        temperature = self.get_zone_value_by_key("current_temperature", zone) / 10
        if unit == "C":
            temperature_celsius = (temperature - 32) / 1.8
            return round(temperature_celsius, 1)

        return temperature

    def set_temperature(self, payload: dict):
        if "temperature" not in payload:
            raise Exception("No temperature found in payload")

        if "zone" not in payload:
            raise Exception("No zone found in payload")

        temperature = payload["temperature"] * 10
        if "unit" not in payload or payload["unit"] == "C":
            temperature = temperature * 1.8 + 320

        temperature_request = replace_keys({
            "controller": payload["controller"] if "controller" in payload else 0,
            "data": {"setpoint_used": temperature},
            "type": "REQ_TH",
            "zone": payload["zone"]
        }, self.mqtt_client.get_referentials())

        installation_unique = self.get_installation_unique_by_zone(payload["zone"])
        return self.mqtt_client.send_message("$client/{}".format(installation_unique), temperature_request)

    def get_energy_level(self, zone: int) -> EnergyLevels:
        energy_level = self.get_zone_value_by_key("energy_level", zone)
        return EnergyLevels(energy_level)

    def set_energy_level(self, payload: dict):
        if "mode" not in payload:
            raise Exception("No mode found in payload")

        if "zone" not in payload:
            raise Exception("No zone found in payload")

        energy_level_request = replace_keys({
            "controller": payload["controller"] if "controller" in payload else 0,
            "data": {"mode_permanent": payload["mode"]},
            "type": "REQ_TH",
            "zone": payload["zone"]
        }, self.mqtt_client.get_referentials())

        installation_unique = self.get_installation_unique_by_zone(payload["zone"])
        return self.mqtt_client.send_message("$client/{}".format(installation_unique), energy_level_request)

    def get_global_energy_level(self):
        self.installations = self.get_installations_as_dict()
        return self.installations[0]["global_energy_level"]

    def set_global_energy_level(self, payload: dict):
        if "mode" not in payload:
            raise Exception("No mode found in payload")

        zones = {}
        for installation in self.get_installations_as_dict():
            zones[installation["unique"]] = []
            for group in installation["groups"]:
                for zone in group["zones"]:
                    zones[installation["unique"]].append(zone["number"])

        for installation_unique, zones in zones.items():
            global_energy_level_request = replace_keys({
                "controller": payload["controller"] if "controller" in payload else 0,
                "data": {"mode_used": payload["mode"], "zone_impacted": zones},
                "type": "REQ_TH",
            }, self.mqtt_client.get_referentials())

            return self.mqtt_client.send_message("$client/{}".format(installation_unique), global_energy_level_request)

    def get_operation_mode(self) -> OperationModes:
        installation = self.get_installations_as_dict()[0]
        return OperationModes(installation["operating_mode"])

    def set_operation_mode(self, payload: dict):
        if "mode" not in payload:
            raise Exception("No mode found in payload")

        # mode to string with 0 padding
        payload["mode"] = str(payload["mode"]).zfill(2)

        operation_mode_request = replace_keys({
            "data": {"heat_cool": payload["mode"]},
            "type": "REQ_TH",
        }, self.mqtt_client.get_referentials())

        if "unique" in payload:
            installation_unique = payload["unique"]
        else:
            installation_unique = self.get_installation_unique_by_zone(payload["zone"])
        return self.mqtt_client.send_message("$client/{}".format(installation_unique), operation_mode_request)

    async def is_connected(self):
        while not self.mqtt_client.is_authenticated() or self.get_installations() is None:
            pass
