"""Sample API Client."""
from __future__ import annotations

import asyncio
import socket

import aiohttp
import async_timeout


class IntegrationRehauNeaSmart2ApiClientError(Exception):
    """Exception to indicate a general API error."""


class IntegrationRehauNeaSmart2ApiClientCommunicationError(
    IntegrationRehauNeaSmart2ApiClientError
):
    """Exception to indicate a communication error."""


class IntegrationRehauNeaSmart2ApiClientAuthenticationError(
    IntegrationRehauNeaSmart2ApiClientError
):
    """Exception to indicate an authentication error."""


class IntegrationRehauNeaSmart2ApiClient:
    """API Client"""

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """API Client"""
        self._url = url
        self._session = session

    async def async_get_health(self) -> bool:
        """Check health"""
        health = await self._api_wrapper(method="get", url=self._url + "/health")
        if health["status"] == "ok":
            return True
        else:
            return False

    async def async_get_settings(self) -> dict:
        """Get settings from the API."""
        return await self._api_wrapper(method="get", url=self._url + "/settings")

    async def async_get_rooms_detailed(self) -> any:
        """Get rooms from the API."""
        return await self._api_wrapper(method="get", url=self._url + "/rooms/detailed")
    
    async def async_get_rooms(self) -> any:
        """Get data from the API."""
        return await self._api_wrapper(method="get", url=self._url + "/rooms")

    async def async_get_room(self, zone) -> any:
        """Get room from the API."""
        return await self._api_wrapper(
            method="get", url=self._url + "/room/" + str(zone)
        )

    async def async_set_room(self, room: dict) -> any:
        """Set room"""
        return await self._api_wrapper(
            method="put",
            url=self._url + "/room/" + str(room["id"]),
            data={"temp": room["target_temp"], "mode": room["mode"]},
        )

    async def async_set_operation_mode(self, mode: str) -> any:
        """Set operation mode"""
        return await self._api_wrapper(
            method="put",
            url=self._url + "/operation_mode",
            data={"operation_mode": mode},
        )

    async def async_set_energy_level(self, level: str) -> any:
        """Set energy level"""
        return await self._api_wrapper(
            method="put",
            url=self._url + "/energy_level",
            data={"energy_level": level},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                if response.status in (401, 403):
                    raise IntegrationRehauNeaSmart2ApiClientAuthenticationError(
                        "Invalid credentials",
                    )
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError as exception:
            raise IntegrationRehauNeaSmart2ApiClientCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise IntegrationRehauNeaSmart2ApiClientCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise IntegrationRehauNeaSmart2ApiClientError(
                "Something really wrong happened!"
            ) from exception
