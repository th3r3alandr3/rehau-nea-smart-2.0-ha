"""Controller module for the REHAU NEA SMART 2 integration."""
from collections.abc import Callable
from .utils import replace_keys, EnergyLevels, OperationModes, ClientTopics
from .handlers import update_temperature, update_energy_level, update_operating_mode
from .models import Installation, Zone
from .MqttClient import MqttClient
from .exceptions import MqttClientError
from homeassistant.core import HomeAssistant


class Controller:
    """Controller class for the REHAU NEA SMART 2 integration."""

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        """Initializ the Controller object.

        Args:
            email (str): The email address for authentication.
            password (str): The password for authentication.
        """
        self.id = "REHAU NEA SMART 2.0"
        self.name = "REHAU NEA SMART 2.0 Climate Control System"
        self.model = "Neasmart 2.0 Base Station"
        self.manufacturer = "Rehau"
        self.auth_username = email
        self.auth_password = password
        self.mqtt_client = None
        self.hass = hass

    async def connect(self):
        """Connect to the MQTT broker and authenticates the user."""
        self.mqtt_client = MqttClient(hass=self.hass, username=self.auth_username, password=self.auth_password)
        await self.mqtt_client.auth_user()

    async def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.mqtt_client.disconnect()

    def is_connected(self, installation_unique: str):
        """Check if the installation is connected to the MQTT broker."""
        Installations = self.get_installations_as_dict()
        if Installations is None:
            return False
        for installation in Installations:
            if installation["unique"] == installation_unique:
                return installation["connected"]


    def is_authenticated(self):
        """Check if the user is authenticated.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        return self.mqtt_client.is_authenticated()

    def get_installations(self) -> list[Installation]:
        """Retrieve the list of installations.

        Returns:
            list[Installation]: The list of installations.
        """
        installations = self.mqtt_client.get_installations()
        if installations is None:
            return None
        return [Installation(**installation) for installation in installations]

    def get_installations_as_dict(self) -> list[dict]:
        """Retrieve the list of installations as a dictionary.

        Returns:
            list[dict]: The list of installations as a dictionary.
        """
        return self.mqtt_client.get_installations()

    def get_zones(self) -> list[Zone]:
        """Retrieve the list of zones.

        Returns:
            list[Zone]: The list of zones.
        """
        zones = []
        for installation in self.get_installations():
            for group in installation.groups:
                for zone in group.zones:
                    zones.append(zone)
        return zones

    def get_zone(self, zone_number: int) -> Zone:
        """Retrieve a specific zone by zone number.

        Args:
            zone_number (int): The zone number.

        Returns:
            Zone: The zone object.

        Raises:
            MqttClientError: If no zone is found for the given zone number.
        """
        for zone in self.get_zones():
            if zone.number == zone_number:
                return zone
        raise MqttClientError("No zone found for zone " + str(zone_number))

    def get_installation_unique_by_zone(self, zone_number: int) -> str:
        """Retrieve the unique installation identifier for a specific zone.

        Args:
            zone_number (int): The zone number.

        Returns:
            str: The unique installation identifier.

        Raises:
            MqttClientError: If no zone is found for the given zone number.
        """
        installations = self.get_installations_as_dict()
        for installation in installations:
            for group in installation["groups"]:
                for zone in group["zones"]:
                    if zone["number"] == zone_number:
                        return installation["unique"]
        raise MqttClientError("No zone found for zone " + str(zone_number))

    def get_zone_value_by_key(self, key: str, zone_number: int):
        """Retrieve the value of a specific key for a specific zone.

        Args:
            key (str): The key to retrieve the value for.
            zone_number (int): The zone number.

        Returns:
            Any: The value of the key.

        Raises:
            MqttClientError: If no zone is found for the given zone number or if no value is found for the key.
        """
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
                                raise MqttClientError(
                                    "No value found for key "
                                    + key
                                    + " in zone "
                                    + str(zone_number)
                                )
                            return sum(values) / len(values)
                        else:
                            raise MqttClientError(
                                "Multiple channels found for zone "
                                + str(zone_number)
                                + " cannot return _id"
                            )
        raise MqttClientError("No zone found for zone " + str(zone_number))

    def get_temperature(self, zone: int, unit="C") -> float:
        """Retrieve the temperature for a specific zone.

        Args:
            zone (int): The zone number.
            unit (str, optional): The unit of temperature. Defaults to "C".

        Returns:
            float: The temperature value.

        Raises:
            MqttClientError: If no zone is found for the given zone number.
        """
        temperature = self.get_zone_value_by_key("current_temperature", zone) / 10
        if unit == "C":
            temperature_celsius = (temperature - 32) / 1.8
            return round(temperature_celsius, 1)

        return temperature

    def set_temperature(self, payload: dict):
        """Set the temperature for a specific zone.

        Args:
            payload (dict): The payload containing the temperature and zone information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the temperature or zone is not found in the payload.
        """
        if "temperature" not in payload:
            raise MqttClientError("No temperature found in payload")

        if "zone" not in payload:
            raise MqttClientError("No zone found in payload")

        temperature = payload["temperature"] * 10
        if "unit" not in payload or payload["unit"] == "C":
            temperature = temperature * 1.8 + 320

        int_temperature = int(temperature)

        temperature_request = replace_keys(
            {
                "controller": payload["controller"] if "controller" in payload else 0,
                "data": {"setpoint_used": int_temperature},
                "type": "REQ_TH",
                "zone": payload["zone"],
            },
            self.mqtt_client.get_referentials(),
        )

        update_temperature(self.get_installations_as_dict(), payload["zone"], int_temperature)
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, temperature_request)

    def get_energy_level(self, zone: int) -> EnergyLevels:
        """Retrieve the energy level for a specific zone.

        Args:
            zone (int): The zone number.

        Returns:
            EnergyLevels: The energy level.

        Raises:
            MqttClientError: If no zone is found for the given zone number.
        """
        energy_level = self.get_zone_value_by_key("energy_level", zone)
        return EnergyLevels(energy_level)

    def set_energy_level(self, payload: dict):
        """Set the energy level for a specific zone.

        Args:
            payload (dict): The payload containing the mode and zone information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode or zone is not found in the payload.
        """
        if "mode" not in payload:
            raise MqttClientError("No mode found in payload")

        if "zone" not in payload:
            raise MqttClientError("No zone found in payload")

        energy_level_request = replace_keys(
            {
                "controller": payload["controller"] if "controller" in payload else 0,
                "data": {"mode_permanent": payload["mode"]},
                "type": "REQ_TH",
                "zone": payload["zone"],
            },
            self.mqtt_client.get_referentials(),
        )

        update_energy_level(self.get_installations_as_dict(), payload["zone"], payload["mode"])
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, energy_level_request)

    def get_global_energy_level(self) -> EnergyLevels:
        """Retrieve the global energy level.

        Returns:
            Any: The global energy level.

        Raises:
            MqttClientError: If no installations are found.
        """
        self.installations = self.get_installations_as_dict()
        return self.installations[0]["global_energy_level"]

    def set_global_energy_level(self, payload: dict):
        """Set the global energy level.

        Args:
            payload (dict): The payload containing the mode information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode is not found in the payload.
        """
        if "mode" not in payload:
            raise MqttClientError("No mode found in payload")

        zones = {}
        for installation in self.get_installations_as_dict():
            zones[installation["unique"]] = []
            for group in installation["groups"]:
                for zone in group["zones"]:
                    zones[installation["unique"]].append(zone["number"])

        for _installation_unique, zones in zones.items():
            global_energy_level_request = replace_keys(
                {
                    "controller": payload["controller"]
                    if "controller" in payload
                    else 0,
                    "data": {"mode_used": payload["mode"], "zone_impacted": zones},
                    "type": "REQ_TH",
                },
                self.mqtt_client.get_referentials(),
            )

            return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, global_energy_level_request)

    def get_operation_mode(self) -> OperationModes:
        """Retrieve the operation mode.

        Returns:
            OperationModes: The operation mode.

        Raises:
            MqttClientError: If no installations are found.
        """
        installation = self.get_installations_as_dict()[0]
        return OperationModes(installation["operating_mode"])

    def set_operation_mode(self, mode: str|int):
        """Set the operation mode.

        Args:
            mode (str|int): The operation mode.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode is not found in the payload.
        """
        if mode is None:
            raise MqttClientError("No mode found in payload")

        # mode to string with 0 padding
        mode = str(mode).zfill(2)

        operation_mode_request = replace_keys(
            {
                "data": {"heat_cool": mode},
                "type": "REQ_TH",
            },
            self.mqtt_client.get_referentials(),
        )


        update_operating_mode(self.get_installations_as_dict(), self.mqtt_client.get_install_id, mode)
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, operation_mode_request)

    def is_ready(self) -> bool:
        """Check if the controller is connected to the MQTT broker.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.mqtt_client.is_ready()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state.

        Args:
            callback (Callable[[], None]): Callback to be called when Roller changes state.
        """
        self.mqtt_client.register_callback(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback.

        Args:
            callback (Callable[[], None]): Callback to be removed.
        """
        self.mqtt_client.remove_callback(callback)

    def get_installation_by_unique(self, installation_unique: str):
            """Return the installation"""
            Installations = self.get_installations_as_dict()
            if Installations is None:
                return False
            for installation in Installations:
                if installation["unique"] == installation_unique:
                    return installation