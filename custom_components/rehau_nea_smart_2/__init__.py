"""Custom integration to integrate rehau_nea_smart_2 with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/rehau_nea_smart_2
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .mqtt.Controller import Controller
from .const import DOMAIN
from .coordinator import RehauNeaSmart2DataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SELECT,
]

# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    controller = Controller(hass, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    await controller.connect()
    hass.data[DOMAIN][f"{entry.entry_id}_controller"] = controller
    hass.data[DOMAIN][entry.entry_id] = coordinator = RehauNeaSmart2DataUpdateCoordinator(
        hass=hass,
        sysname="REHAU NEA SMART 2.0",
        controller=controller,
    )
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await controller.is_connected()
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    controller: Controller = hass.data[DOMAIN][f"{entry.entry_id}_controller"]
    controller.disconnect()
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
