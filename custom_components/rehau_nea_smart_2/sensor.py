"""Sensor platform for rehau_nea_smart_2."""

from __future__ import annotations
import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.const import (
    TEMPERATURE,
    UnitOfTemperature,
)

from .mqtt import Installation, Zone

from .const import DOMAIN
from .coordinator import RehauNeaSmart2DataUpdateCoordinator
from .entity import IntegrationRehauNeaSmart2Entity

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="rehau_nea_smart_2",
        name="Integration Sensor",
        icon="mdi:thermometer",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    installations: list[Installation] = await coordinator._async_update_data()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        for installation in installations:
            for group in installation.groups:
                for zone in group.zones:
                    devices.append(
                        RehauNeasmart2TemperatureSensor(
                            coordinator, zone, entity_description
                        )
                    )

    async_add_devices(devices)


class IntegrationRehauNeaSmart2Sensor(IntegrationRehauNeaSmart2Entity, SensorEntity):
    """rehau_nea_smart_2 Sensor class."""

    def __init__(
            self,
            coordinator: RehauNeaSmart2DataUpdateCoordinator,
            entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return "15"


class RehauNeasmartGenericSensor(SensorEntity, RestoreEntity):
    """Generic sensor class for Rehau Neasmart."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, zone: Zone):
        """Initialize the generic sensor class."""
        self._zone = zone
        self._coordinator = coordinator
        self._available = True
        self._zone_number = zone.number
        self._name = zone.name
        self._state = round((zone.channels[0].current_temperature / 10 - 32) / 1.8, 1)

    @property
    def device_info(self):
        """Return device information for the sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.id)},
            name=self._coordinator.name,
            manufacturer=self._coordinator.manufacturer,
            model=self._coordinator.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the sensor is available, False otherwise."""
        return self._available

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self._state


class RehauNeasmart2TemperatureSensor(RehauNeasmartGenericSensor):
    """Temperature sensor class for Rehau Neasmart 2."""

    device_class = TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
            self,
            coordinator,
            zone: Zone,
            entity_description: SensorEntityDescription,
    ):
        """Initialize the temperature sensor class."""
        super().__init__(coordinator, zone)
        self._attr_unique_id = f"{self._zone}_temperature"
        self._attr_name = f"{self._name} Temperature"
        self.entity_description = entity_description

    async def async_update(self) -> None:
        """Update the temperature sensor."""
        temperature = self._coordinator.get_temperature(self._zone_number)
        if temperature is not None:
            self._state = temperature
        else:
            _LOGGER.error(f"Error updating {self._zone.name} temperature")
