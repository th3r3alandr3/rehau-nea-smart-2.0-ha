"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector

from .mqtt import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
    MqttClientError,
    MqttClient,
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
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
            except MqttClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MqttClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MqttClientError as exception:
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
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL
                        ),
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                        default=(user_input or {}).get(CONF_PASSWORD),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, email: str, password: str) -> None:
        """Validate credentials."""
        try:
            result = await MqttClient.check_credentials(email=email, password=password, hass=self.hass)
            print(result)
            print("Connected to REHAU Nea Smart 2.0 API")
        except Exception as exception:
            print(exception)
            print("Could not connect to REHAU Nea Smart 2.0 API")
            raise MqttClientAuthenticationError from exception
