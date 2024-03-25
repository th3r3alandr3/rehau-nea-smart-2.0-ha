"""Select platform for rehau_nea_smart_2."""

from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

from .rehau_mqtt_client import Installation
from .rehau_mqtt_client.Controller import Controller

from .const import DOMAIN, PRESET_OPERATING_MODES_MAPPING, PRESET_ENERGY_LEVELS_MAPPING, \
    PRESET_OPERATING_MODES_MAPPING_REVERSE, PRESET_ENERGY_LEVELS_MAPPING_REVERSE

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
    controller: Controller = hass.data[DOMAIN][entry.entry_id]

    installations: list[Installation] = controller.get_installations()
    installation = installations[0]
    operation_mode = installation.operating_mode
    energy_level = installation.global_energy_level

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        devices.append(RehauNeaSmart2OperationModeSelect(controller, entity_description, operation_mode,
                                                         unique=installation.unique))
        devices.append(RehauNeaSmart2OperationEnergyLevelSelect(controller, entity_description, energy_level,
                                                                unique=installation.unique))

    async_add_devices(devices)


class RehauNeaSmart2GenericSelect(SelectEntity, RestoreEntity):
    """Generic Select class for rehau_nea_smart_2."""

    _attr_has_entity_name = False
    should_poll = False

    def __init__(self, controller: Controller, key: str, unique: str):
        """Initialize the Generic Select class."""
        self._controller = controller
        self._available = True
        self._trans_key = key
        self._unique = unique

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._controller.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Run when this Entity will be removed from HA."""
        self._controller.remove_callback(self.async_write_ha_state)

    @property
    def device_info(self):
        """Return device information for the Select."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._controller.id)},
            name=self._controller.name,
            manufacturer=self._controller.manufacturer,
            model=self._controller.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the climate entity is available."""
        return self._controller.is_connected(self._unique)

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

    def __init__(self, controller: Controller, entity_description: SelectEntityDescription,
                 operation_mode: str, unique: str):
        """Initialize the Operation Mode Select class."""
        super().__init__(controller, "climate_mode", unique)
        self._attr_unique_id = f"{self._controller.id}_operation_climate_mode"
        self._attr_name = "Climate Mode"
        self.entity_description = entity_description
        self._attr_options = [option for option in PRESET_OPERATING_MODES_MAPPING.keys() if option not in ["unknown"]]
        self._attr_current_option = PRESET_OPERATING_MODES_MAPPING_REVERSE[operation_mode]

    async def async_select_option(self, mode: str) -> None:
        """Select an operation mode."""
        mode = PRESET_OPERATING_MODES_MAPPING[mode]
        _LOGGER.debug(f"Setting operation mode to {mode}")
        if not self._controller.set_operation_mode(mode):
            _LOGGER.error(f"Error configuring {mode} operation climate mode")

    @property
    def current_option(self):
        """Returns the current option for the select entity.

        If the operating mode of the installation is available, it returns the corresponding preset operating mode.
        Otherwise, it returns the current option attribute.

        Returns:
            The current option for the select entity.
        """
        installations: list[Installation] = self._controller.get_installations()
        installation = installations[0]
        operation_mode = installation.operating_mode
        if operation_mode is not None:
            return PRESET_OPERATING_MODES_MAPPING_REVERSE[operation_mode]

        return self._attr_current_option



class RehauNeaSmart2OperationEnergyLevelSelect(RehauNeaSmart2GenericSelect):
    """Operation Energy Level Select class for rehau_nea_smart_2."""

    def __init__(self, controller: Controller, entity_description: SelectEntityDescription,
                 energy_level: str, unique: str):
        """Initialize the Operation Energy Level Select class."""
        super().__init__(controller, "energy_level", unique)
        self._attr_unique_id = f"{self._controller.id}_energy_level"
        self._attr_name = "Energy level"
        self.entity_description = entity_description
        self._attr_options = list(PRESET_ENERGY_LEVELS_MAPPING.keys())
        self._attr_current_option = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[energy_level]

    async def async_select_option(self, energy_level: str) -> None:
            """Select the specified energy level.

            Args:
                energy_level (str): The energy level to select.

            Returns:
                None
            """
            energy_level = PRESET_ENERGY_LEVELS_MAPPING[energy_level]
            _LOGGER.debug(f"Setting energy level to {energy_level}")
            if not self._controller.set_global_energy_level({"mode": energy_level}):
                _LOGGER.error(f"Error configuring {energy_level} energy level")


    @property
    def current_option(self):
        """Returns the current option for the select component.

        If the global energy level is available, it returns the corresponding preset energy level.
        Otherwise, it returns the current option set for the select component.

        Returns:
            The current option for the select component.
        """
        installations: list[Installation] = self._controller.get_installations()
        installation = installations[0]
        energy_level = installation.global_energy_level
        if energy_level is not None:
            return PRESET_ENERGY_LEVELS_MAPPING_REVERSE[energy_level]

        return self._attr_current_option
