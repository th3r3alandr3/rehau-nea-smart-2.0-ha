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

from .api import (
    IntegrationRehauNeaSmart2ApiClient,
    IntegrationRehauNeaSmart2ApiClientAuthenticationError,
    IntegrationRehauNeaSmart2ApiClientError,
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
        client: IntegrationRehauNeaSmart2ApiClient,
    ) -> None:
        """Initialize the RehauNeaSmart2DataUpdateCoordinator.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            sysname (str): The system name.
            client (IntegrationRehauNeaSmart2ApiClient): The API client.
        """
        self.client = client
        self.name = f"{sysname} Climate Control System"
        self.model = "Neasmart 2.0 Base Station"
        self.manufacturer = "Rehau"
        self.online = True
        self.id = sysname
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def async_get_health(self) -> bool:
        """Get health from the API.

        Returns:
            bool: True if the API is healthy, False otherwise.
        """
        try:
            return await self.client.async_get_health()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError:
            return False
        except IntegrationRehauNeaSmart2ApiClientError:
            return False

    async def async_get_settings(self) -> dict:
        """Get settings from the API.

        Returns:
            dict: The settings retrieved from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the settings.
        """
        try:
            return await self.client.async_get_settings()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def _async_update_data(self) -> list:
        """Update data via library.

        Returns:
            list: The updated data retrieved from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error updating the data.
        """
        try:
            return await self.client.async_get_rooms()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_get_rooms_detailed(self) -> list:
        """Get detailed information about the rooms from the Rehau Nea Smart 2 API.

        Returns:
            list: A list of detailed room information.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room information.
        """
        try:
            return await self.client.async_get_rooms_detailed()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_get_rooms(self) -> list:
        """Get rooms from the API.

        Returns:
            list: The rooms retrieved from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the rooms.
        """
        try:
            return await self.client.async_get_rooms()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def get_room(self, zone) -> float | None:
        """Get the room temperature.

        Args:
            zone: The zone of the room.

        Returns:
            float | None: The current temperature of the room, or None if not available.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error retrieving the room temperature.
        """
        try:
            return await self.client.async_get_room(zone)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def get_temperature(self, zone) -> float | None:
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
            room = await self.client.async_get_room(zone)
            return room["current_temp"]
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_set_room(self, room: dict) -> any:
        """Set the room settings.

        Args:
            room (dict): The room settings.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the room.
        """
        try:
            return await self.client.async_set_room(room)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_set_operation_mode(self, mode: str) -> any:
        """Set the operation mode.

        Args:
            mode (str): The operation mode.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the operation mode.
        """
        try:
            return await self.client.async_set_operation_mode(mode)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_set_energy_level(self, level: str) -> any:
        """Set the energy level.

        Args:
            level (str): The energy level.

        Returns:
            any: The response from the API.

        Raises:
            ConfigEntryAuthFailed: If authentication with the API fails.
            UpdateFailed: If there is an error setting the energy level.
        """
        try:
            return await self.client.async_set_energy_level(level)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception
