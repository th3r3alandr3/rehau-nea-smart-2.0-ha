"""Select platform for rehau_nea_smart_2."""

from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, PRESET_CLIMATE_MODES_MAPPING, PRESET_ENERGY_LEVELS_MAPPING
from .coordinator import RehauNeaSmart2DataUpdateCoordinator
from .entity import IntegrationRehauNeaSmart2Entity

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    SelectEntityDescription(
        key="rehau_nea_smart_2",
        name="Integration Select",
        icon="mdi:home",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the Select platform."""
    coordinator: RehauNeaSmart2DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    settings = await coordinator.async_get_settings()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        devices.append(RehauNeaSmart2OperationModeSelect(coordinator, entity_description, settings["operation_mode"]))
        devices.append(RehauNeaSmart2OperationEnergyLevelSelect(coordinator, entity_description, settings["energy_level"]))

    async_add_devices(devices)


class IntegrationRehauNeaSmart2Select(IntegrationRehauNeaSmart2Entity, SelectEntity):
    """rehau_nea_smart_2 Select class."""

    def __init__(
        self,
        coordinator: RehauNeaSmart2DataUpdateCoordinator,
        entity_description: SelectEntityDescription,
    ) -> None:
        """Initialize the Select class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str:
        """Return the native value of the Select."""
        return "15"


class RehauNeaSmartGenericSelect(SelectEntity, RestoreEntity):
    """Generic Select class for rehau_nea_smart_2."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, key: str):
        """Initialize the Generic Select class."""
        self._coordinator = coordinator
        self._available = True
        self._trans_key = key

    @property
    def device_info(self):
        """Return device information for the Select."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.id)},
            name=self._coordinator.name,
            manufacturer=self._coordinator.manufacturer,
            model=self._coordinator.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the Select is available."""
        return self._available

    @property
    def native_value(self) -> float | None:
        """Return the native value of the Select."""
        return self._state

    @property
    def translation_key(self) -> str:
        """Return the translation key of the Select."""
        return self._trans_key


class RehauNeaSmart2OperationModeSelect(RehauNeaSmartGenericSelect):
    """Operation Mode Select class for rehau_nea_smart_2."""

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, entity_description: SelectEntityDescription, operation_mode: str):
        """Initialize the Operation Mode Select class."""
        super().__init__(coordinator, "climate_mode")
        self._attr_unique_id = f"{self._coordinator.id}_operation_climate_mode"
        self._attr_name = "Climate Mode"
        self.entity_description = entity_description
        self._attr_options = list(PRESET_CLIMATE_MODES_MAPPING.keys())
        self._attr_current_option = operation_mode

    async def async_select_option(self, mode: str) -> None:
        """Select an operation mode."""
        if not await self._coordinator.async_set_operation_mode(mode):
            _LOGGER.error(f"Error configuring {mode} operation climate mode")

    async def async_update(self) -> None:
        """Update the Select."""
        settings = await self._coordinator.async_get_settings()
        operation_mode = settings["operation_mode"]
        if operation_mode is not None:
            self._attr_current_option = operation_mode
        else:
            _LOGGER.error(f"Error updating {self._attr_name}_operation_climate_mode")


class RehauNeaSmart2OperationEnergyLevelSelect(RehauNeaSmartGenericSelect):
    """Operation Energy Level Select class for rehau_nea_smart_2."""

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, entity_description: SelectEntityDescription, energy_level: str):
        """Initialize the Operation Energy Level Select class."""
        super().__init__(coordinator, "energy_level")
        self._attr_unique_id = f"{self._coordinator.id}_energy_level"
        self._attr_name = "Energy level"
        self.entity_description = entity_description
        self._attr_options = list(PRESET_ENERGY_LEVELS_MAPPING.keys())
        self._attr_current_option = energy_level

    async def async_select_option(self, energy_level: str) -> None:
        """Select an energy level."""
        if not await self._coordinator.async_set_energy_level(energy_level):
            _LOGGER.error(f"Error configuring {energy_level} energy level")

    async def async_update(self) -> None:
        """Update the Select."""
        settings = await self._coordinator.async_get_settings()
        energy_level = settings["energy_level"]
        if energy_level is not None:
            self._attr_current_option = energy_level
        else:
            _LOGGER.error(f"Error updating {self._attr_name}_energy_level")
