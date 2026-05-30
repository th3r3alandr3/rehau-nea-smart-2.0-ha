"""Config flow for the Rehau Nea Smart 2 integration.

REHAU's cloud login now enforces e-mail based two-factor authentication, so the
flow is two steps:

1. ``user`` - collect e-mail + password and start the OAuth login.
2. ``mfa`` - REHAU e-mails a 6-digit code; the user types it here.

The resulting refresh token is stored in the config entry so MFA is only needed
once (and again on re-authentication if the refresh token is ever revoked).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector

from .rehau_mqtt_client import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
    MqttClientError,
)
from .rehau_mqtt_client.handlers.auth import RehauAuthSession

from .const import CONF_TOKEN_DATA, DOMAIN, LOGGER

CONF_CODE = "code"


class RehauNeaSmart2FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Rehau Nea Smart 2."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow handler."""
        self._session: RehauAuthSession | None = None
        self._email: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle the credentials step."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._session = RehauAuthSession()
            try:
                result, token_data, _user = await self._session.start(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except MqttClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MqttClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except Exception as exception:  # noqa: BLE001 - surface as unknown
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                if result == "complete":
                    return await self._finish(token_data)
                # MFA required - request the code e-mail and move on.
                try:
                    await self._session.request_email_code()
                except (
                    MqttClientCommunicationError,
                    MqttClientAuthenticationError,
                ) as exception:
                    LOGGER.error(exception)
                    _errors["base"] = "connection"
                else:
                    return await self.async_step_mfa()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL, self._email),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def async_step_mfa(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle the 2FA verification code step."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            try:
                token_data, _user = await self._session.submit_code(
                    user_input[CONF_CODE].strip()
                )
            except MqttClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "invalid_code"
            except MqttClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except Exception as exception:  # noqa: BLE001
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return await self._finish(token_data)

        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.FlowResult:
        """Handle re-authentication when the stored token is no longer valid."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._email = entry_data.get(CONF_EMAIL)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Collect the password again and restart the login (with MFA)."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            self._session = RehauAuthSession()
            try:
                result, token_data, _user = await self._session.start(
                    self._email, user_input[CONF_PASSWORD]
                )
            except MqttClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MqttClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except Exception as exception:  # noqa: BLE001
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                if result == "complete":
                    return await self._finish(token_data)
                try:
                    await self._session.request_email_code()
                except (
                    MqttClientCommunicationError,
                    MqttClientAuthenticationError,
                ) as exception:
                    LOGGER.error(exception)
                    _errors["base"] = "connection"
                else:
                    return await self.async_step_mfa()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            description_placeholders={"email": self._email or ""},
            errors=_errors,
        )

    async def _finish(self, token_data: dict) -> config_entries.FlowResult:
        """Persist the token data and create/update the config entry."""
        data = {CONF_EMAIL: self._email, CONF_TOKEN_DATA: token_data}

        if self._reauth_entry is not None:
            return self.async_update_reload_and_abort(
                self._reauth_entry, data=data
            )

        await self.async_set_unique_id(self._email.lower())
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="REHAU Nea Smart 2.0 API",
            data=data,
        )
