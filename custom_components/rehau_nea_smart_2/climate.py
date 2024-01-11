"""Platform for climate integration."""
import json
import logging
from .coordinator import (
    RehauNeaSmart2DataUpdateCoordinator,
)
from .mqtt.types.installation import Installation, Zone
from .const import (
    DOMAIN,
    NAME,
    VERSION,
    PRESET_ENERGY_LEVELS_MAPPING,
    PRESET_ENERGY_LEVELS_MAPPING_REVERSE,
    PRESET_CLIMATE_MODES_MAPPING,
    PRESET_CLIMATE_MODES_MAPPING_REVERSE,
)
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import ATTR_TEMPERATURE

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    ClimateEntityDescription(
        key="rehau_nea_smart_2",
        name="Integration Climate",
        icon="mdi:home-thermometer",
        translation_key="rehauneasmart2",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the climate platform."""
    coordinator: RehauNeaSmart2DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    installations: list[Installation] = await coordinator._async_update_data()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        for installation in installations:
            for group in installation.groups:
                for zone in group.zones:
                    devices.append(
                        RehauNeaSmart2RoomClimate(coordinator, zone, installation.operating_mode, entity_description)
                    )

    async_add_devices(devices)


class IntegrationRehauNeaSmart2Climate(ClimateEntity, RestoreEntity):
    """Representation of a Rehau Nea Smart 2 climate entity."""

    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, zone: Zone, operating_mode: str):
        """Initialize the Rehau Nea Smart 2 climate entity."""
        self._coordinator = coordinator
        self._state = None
        self._available = True
        channel = zone.channels[0]

        attributes = {
            "id": zone.id,
            "name": zone.name,
            "zone_number": zone.number,
            "current_temp": channel.current_temperature,
            "target_temp": channel.target_temperature,
            "mode": channel.energy_level,
            "max_temp": channel.setpoints.max,
            "min_temp": channel.setpoints.min,
            "operation_mode": operating_mode,
            "heating_normal": channel.setpoints.heating.normal,
            "heating_reduced": channel.setpoints.heating.reduced,
            "heating_standby" : channel.setpoints.heating.standby,
            "cooling_normal": channel.setpoints.cooling.normal,
            "cooling_reduced": channel.setpoints.cooling.reduced,
        }

        for attribute in attributes:
            setattr(self, f"_{attribute}", attributes[attribute])

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )

    @property
    def device_info(self):
        """Return device information for the climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.id)},
            name=self._coordinator.name,
            manufacturer=self._coordinator.manufacturer,
            model=self._coordinator.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the climate entity is available."""
        return True


class RehauNeaSmart2RoomClimate(IntegrationRehauNeaSmart2Climate):
    """Representation of a Rehau Nea Smart 2 room climate entity."""

    def __init__(
        self,
        coordinator: RehauNeaSmart2DataUpdateCoordinator,
        zone,
        operating_mode,
        entity_description: ClimateEntityDescription,
    ):
        """Initialize the Rehau Nea Smart 2 room climate entity."""
        super().__init__(coordinator, zone, operating_mode)
        self._attr_unique_id = f"{self._id}_thermostat"
        self._attr_name = f"{self._name} Thermostat"
        self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.COOL]
        self._attr_preset_modes = list(PRESET_ENERGY_LEVELS_MAPPING.keys())
        self.entity_description = entity_description

        self._attr_preset_mode = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[self._mode]
        self._attr_hvac_mode = PRESET_CLIMATE_MODES_MAPPING[self._operation_mode]
        self._attr_current_temperature = self.format_temperature(self._current_temp)
        self._attr_target_temperature = self.format_temperature(self._target_temp)
        self._attr_max_temp = self.format_temperature(self._max_temp)
        self._attr_min_temp = self.format_temperature(self._min_temp)

    def format_temperature(self, temperature):
        """Format the temperature."""
        return round((temperature / 10 - 32) / 1.8, 1)

    async def async_update(self) -> None:
        """Update the state of the climate entity."""
        zone = self._coordinator.get_zone(self._zone_number)

        if zone is not None:
            channel = zone.channels[0]
            self._attr_current_temperature = self.format_temperature(channel.current_temperature)
            self._attr_target_temperature = self.format_temperature(channel.target_temperature)
            self._attr_preset_mode = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[channel.energy_level]
            self._attr_hvac_mode = PRESET_CLIMATE_MODES_MAPPING[channel.operating_mode]
            self._operation = channel.operating_mode
        else:
            _LOGGER.error(f"Error updating {self._attr_unique_id} thermostat")

    async def async_set_preset_mode(self, preset_mode: str):
        """Set the preset mode of the climate entity."""
        mode = PRESET_ENERGY_LEVELS_MAPPING[preset_mode]
        print(f"Setting mode to {mode}")
        self._coordinator.set_energy_level(self._zone_number, mode)


    async def async_set_temperature(self, **kwargs):
        """Set the target temperature of the climate entity."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        print(f"Setting temperature to {temperature}")
        self._coordinator.set_temperature(self._zone_number, temperature)

    async def async_set_hvac_mode(self, hvac_mode: str):
        """Set the HVAC mode of the climate entity."""
        operation_mode = PRESET_CLIMATE_MODES_MAPPING_REVERSE[hvac_mode]
        print(f"Setting operation mode to {operation_mode}")
        self._coordinator.set_operation_mode(self._zone_number, operation_mode)