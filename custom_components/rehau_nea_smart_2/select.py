"""Select platform for rehau_nea_smart_2."""

from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

from .rehau_mqtt_client import Installation

from .const import DOMAIN, PRESET_OPERATING_MODES_MAPPING, PRESET_ENERGY_LEVELS_MAPPING, \
    PRESET_OPERATING_MODES_MAPPING_REVERSE, PRESET_ENERGY_LEVELS_MAPPING_REVERSE
from .coordinator import RehauNeaSmart2DataUpdateCoordinator

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

    installations: list[Installation] = await coordinator._async_update_data()
    installation = installations[0]
    operation_mode = installation.operating_mode
    energy_level = installation.global_energy_level

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        devices.append(RehauNeaSmart2OperationModeSelect(coordinator, entity_description, operation_mode,
                                                         unique=installation.unique))
        devices.append(RehauNeaSmart2OperationEnergyLevelSelect(coordinator, entity_description, energy_level,
                                                                unique=installation.unique))

    async_add_devices(devices)


class RehauNeaSmart2GenericSelect(SelectEntity, RestoreEntity):
    """Generic Select class for rehau_nea_smart_2."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, key: str, unique: str):
        """Initialize the Generic Select class."""
        self._coordinator = coordinator
        self._available = True
        self._trans_key = key
        self._unique = unique

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


class RehauNeaSmart2OperationModeSelect(RehauNeaSmart2GenericSelect):
    """Operation Mode Select class for rehau_nea_smart_2."""

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, entity_description: SelectEntityDescription,
                 operation_mode: str, unique: str):
        """Initialize the Operation Mode Select class."""
        super().__init__(coordinator, "climate_mode", unique)
        self._attr_unique_id = f"{self._coordinator.id}_operation_climate_mode"
        self._attr_name = "Climate Mode"
        self.entity_description = entity_description
        self._attr_options = list(PRESET_OPERATING_MODES_MAPPING.keys())
        self._attr_current_option = PRESET_OPERATING_MODES_MAPPING_REVERSE[operation_mode]

    async def async_select_option(self, mode: str) -> None:
        """Select an operation mode."""
        mode = PRESET_OPERATING_MODES_MAPPING[mode]
        _LOGGER.debug(f"Setting operation mode to {mode}")
        if not self._coordinator.set_operation_mode_global(self._unique, mode):
            _LOGGER.error(f"Error configuring {mode} operation climate mode")

    async def async_update(self) -> None:
        """Update the Select."""

        installations: list[Installation] = await self._coordinator._async_update_data()
        installation = installations[0]
        operation_mode = installation.operating_mode
        if operation_mode is not None:
            self._attr_current_option = PRESET_OPERATING_MODES_MAPPING_REVERSE[operation_mode]
        else:
            _LOGGER.error(f"Error updating {self._attr_name}_operation_climate_mode")


class RehauNeaSmart2OperationEnergyLevelSelect(RehauNeaSmart2GenericSelect):
    """Operation Energy Level Select class for rehau_nea_smart_2."""

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, entity_description: SelectEntityDescription,
                 energy_level: str, unique: str):
        """Initialize the Operation Energy Level Select class."""
        super().__init__(coordinator, "energy_level", unique)
        self._attr_unique_id = f"{self._coordinator.id}_energy_level"
        self._attr_name = "Energy level"
        self.entity_description = entity_description
        self._attr_options = list(PRESET_ENERGY_LEVELS_MAPPING.keys())
        self._attr_current_option = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[energy_level]

    async def async_select_option(self, energy_level: str) -> None:
        """Select an energy level."""
        energy_level = PRESET_ENERGY_LEVELS_MAPPING[energy_level]
        _LOGGER.debug(f"Setting energy level to {energy_level}")
        if not self._coordinator.set_global_energy_level(energy_level):
            _LOGGER.error(f"Error configuring {energy_level} energy level")

    async def async_update(self) -> None:
        """Update the Select."""
        installations: list[Installation] = await self._coordinator._async_update_data()
        installation = installations[0]
        energy_level = installation.global_energy_level
        if energy_level is not None:
            self._attr_current_option = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[energy_level]
        else:
            _LOGGER.error(f"Error updating {self._attr_name}_energy_level")
