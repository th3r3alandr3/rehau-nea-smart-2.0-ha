"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    IntegrationRehauNeaSmart2ApiClient,
    IntegrationRehauNeaSmart2ApiClientAuthenticationError,
    IntegrationRehauNeaSmart2ApiClientCommunicationError,
    IntegrationRehauNeaSmart2ApiClientError,
)
from .const import DOMAIN, LOGGER


class RehauNeaSmart2FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    url=user_input[CONF_URL],
                )
            except IntegrationRehauNeaSmart2ApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except IntegrationRehauNeaSmart2ApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except IntegrationRehauNeaSmart2ApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="REHAU Nea Smart 2.0 API",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=(user_input or {}).get(CONF_URL),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, url: str) -> None:
        """Validate credentials."""
        client = IntegrationRehauNeaSmart2ApiClient(
            url=url,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_health()
