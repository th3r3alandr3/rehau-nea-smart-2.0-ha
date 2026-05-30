"""Custom integration to integrate rehau_nea_smart_2 with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/rehau_nea_smart_2
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed

from .rehau_mqtt_client.Controller import Controller
from .rehau_mqtt_client.exceptions import MqttClientAuthenticationError
from .const import CONF_TOKEN_DATA, DOMAIN

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SELECT,
]

# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    @callback
    def persist_token(token_data: dict) -> None:
        """Persist refreshed token data back to the config entry."""
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN_DATA: token_data}
        )

    @callback
    def trigger_reauth() -> None:
        """Start Home Assistant's re-authentication flow."""
        entry.async_start_reauth(hass)

    controller = Controller(
        hass,
        entry.data[CONF_EMAIL],
        token_data=entry.data.get(CONF_TOKEN_DATA),
        on_token_update=persist_token,
        on_auth_failed=trigger_reauth,
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    try:
        await controller.connect()
    except MqttClientAuthenticationError as err:
        raise ConfigEntryAuthFailed(
            "REHAU re-authentication required (login expired)"
        ) from err
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        controller: Controller = hass.data[DOMAIN].pop(entry.entry_id)
        await controller.disconnect()
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
