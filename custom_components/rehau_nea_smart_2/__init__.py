"""Custom integration to integrate rehau_nea_smart_2 with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/rehau_nea_smart_2
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .rehau_mqtt_client.Controller import Controller
from .const import DOMAIN

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SELECT,
]

# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    controller = Controller(hass, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    await controller.connect()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        controller: Controller = hass.data[DOMAIN].pop(entry.entry_id)
        await controller.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
