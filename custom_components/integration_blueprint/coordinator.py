"""DataUpdateCoordinator for integration_blueprint."""
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


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class RehauNeaSmart2DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        sysname: str,
        client: IntegrationRehauNeaSmart2ApiClient,
    ) -> None:
        """Initialize."""
        self.client = client
        self.name = "{} Climate Control System".format(sysname)
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
        """Get health from the API."""
        try:
            return await self.client.async_get_health()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            return False
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            return False

    async def async_get_settings(self) -> dict:
        """Get settings from the API."""
        try:
            return await self.client.async_get_settings()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def _async_update_data(self) -> list:
        """Update data via library."""
        try:
            return await self.client.async_get_rooms()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_get_rooms_detailed(self) -> list:
        try:
            return await self.client.async_get_rooms_detailed()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_get_rooms(self) -> list:
        try:
            return await self.client.async_get_rooms()
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def get_room(self, zone) -> float | None:
        try:
            return await self.client.async_get_room(zone)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def get_temperature(self, zone) -> float | None:
        try:
            room = await self.client.async_get_room(zone)
            return room["current_temp"]
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_set_room(self, room: dict) -> any:
        try:
            print(room)
            return await self.client.async_set_room(room)
        except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationRehauNeaSmart2ApiClientError as exception:
            raise UpdateFailed(exception) from exception
