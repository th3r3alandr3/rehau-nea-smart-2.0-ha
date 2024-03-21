"""DataUpdateCoordinator for rehau_nea_smart_2."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .rehau_mqtt_client import (
    MqttClientAuthenticationError,
    MqttClientError,
    Installation,
    Zone,
    Controller,
)

from .const import DOMAIN, LOGGER


class RehauNeaSmart2DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API.

    This coordinator is responsible for fetching data from the Rehau Nea Smart 2 API.
    It handles authentication errors, update failures, and provides methods to retrieve
    various data from the API.
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        sysname: str,
        controller: Controller,
    ) -> None:
        """Initialize the RehauNeaSmart2DataUpdateCoordinator.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            sysname (str): The system name.
            controller (Controller): The controller instance.
        """
        self.controller = controller
        self.name = f"{sysname} Climate Control System"
        self.model = "Neasmart 2.0 Base Station"
        self.manufacturer = "Rehau"
        self.online = True
        self.id = sysname
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )

    def is_connected(self, installation_unique: str) -> bool:
        """Get connection status.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.controller.is_connected(installation_unique)

    async def async_get_health(self) -> bool:
        """Get health from the API.

        Returns:
            bool: True if the API is healthy, False otherwise.
        """
        try:
            return await self.controller.is_authenticated()
        except MqttClientAuthenticationError:
            return False
        except MqttClientError:
            return False

    async def _async_update_data(self) -> list[Installation]:
        """Update data via library.

        Returns:
            list: The updated data retrieved from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error updating the data.
        """
        try:
            return self.controller.get_installations()
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_zone(self, zone) -> Zone:
        """Get zones from the API.

        Returns:
            dict: The zones retrieved from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the zones.
        """
        try:
            return self.controller.get_zone(zone)
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_temperature(self, zone) -> float | None:
        """Get the current temperature of a room.

        Args:
            zone: The zone of the room.

        Returns:
            float | None: The current temperature of the room, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room temperature.
        """
        try:
            return self.controller.get_temperature(zone)
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def set_temperature(self, zone, temperature) -> float | None:
        """Set the target temperature of a room.

        Args:
            zone: The zone of the room.
            temperature: The target temperature of the room.

        Returns:
            float | None: The current temperature of the room, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room temperature.
        """
        try:
            return self.controller.set_temperature(
                {"zone": zone, "temperature": temperature}
            )
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_operation_mode(self, zone) -> str | None:
        """Get the operation mode of a room.

        Args:
            zone: The zone of the room.

        Returns:
            str | None: The operation mode of the room, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room operation mode.
        """
        try:
            return self.controller.get_operation_mode(zone)
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def set_operation_mode(self, zone: int, mode: str) -> any:
        """Set the operation mode.

        This method sets the operation mode for a specific zone.

        Args:
            zone (int): The zone number.
            mode (str): The operation mode.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the operation mode.
        """
        try:
            return self.controller.set_operation_mode({"zone": zone, "mode": mode})
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def set_operation_mode_global(self, install_unique: str, mode: str) -> any:
        """Set the operation mode globally for all devices.

        This method sets the operation mode for all devices associated with the given installation unique identifier.

        Args:
            install_unique (str): The unique identifier of the installation.
            mode (str): The operation mode to set.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the operation mode.
        """
        try:
            return self.controller.set_operation_mode(
                {"unique": install_unique, "mode": mode}
            )
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_energy_level(self, zone) -> str | None:
        """Get the energy level of a room.

        Args:
            zone (str): The zone of the room.

        Returns:
            str | None: The energy level of the room, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room energy level.
        """
        try:
            return self.controller.get_energy_level(zone)
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def set_energy_level(self, zone: int, level: str) -> any:
        """Set the energy level.

        Args:
            zone (int): The zone identifier.
            level (str): The energy level.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the energy level.
        """
        try:
            return self.controller.set_energy_level({"zone": zone, "mode": level})
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_global_energy_level(self) -> str | None:
        """Get the global energy level.

        Returns:
            str | None: The global energy level, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the global energy level.
        """
        try:
            return self.controller.get_global_energy_level()
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception

    def set_global_energy_level(self, level: str) -> any:
        """Set the global energy level.

        Args:
            level (str): The global energy level.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the global energy level.
        """
        try:
            return self.controller.set_global_energy_level({"mode": level})
        except MqttClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MqttClientError as exception:
            raise UpdateFailed(exception) from exception
