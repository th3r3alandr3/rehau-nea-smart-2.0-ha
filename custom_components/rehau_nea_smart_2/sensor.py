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

from .rehau_mqtt_client import Installation, Zone
from .rehau_mqtt_client.Controller import Controller

from .const import DOMAIN

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
    controller: Controller = hass.data[DOMAIN][entry.entry_id]

    installations: list[Installation] = controller.get_installations()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        for installation in installations:
            devices.append(
                RehauNeasmart2OutdoorTemperatureSensor(
                    controller, installation, "outside_temp", "Outside Temperature", entity_description
                )
            )
            devices.append(
                RehauNeasmart2OutdoorTemperatureSensor(
                    controller, installation, "outsideTempFiltered", "Filtered Outside Temperature", entity_description
                )
            )
            for group in installation.groups:
                for zone in group.zones:
                    devices.append(
                        RehauNeasmart2TemperatureSensor(
                            controller, zone, installation.unique, entity_description
                        )
                    )

    async_add_devices(devices)


class RehauNeasmartGenericSensor(SensorEntity, RestoreEntity):
    """Generic sensor class for Rehau Neasmart."""

    _attr_has_entity_name = False
    should_poll = False

    def __init__(self, controller: Controller, zone: Zone, installation_unique: str):
        """Initialize the generic sensor class."""
        self._zone = zone
        self._controller = controller
        self._available = True
        self._id = zone.id
        self._zone_number = zone.number
        self._name = zone.name
        self._installation_unique = installation_unique
        self._state = round((zone.channels[0].current_temperature / 10 - 32) / 1.8, 1)

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._controller.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Run when this Entity will be removed from HA."""
        self._controller.remove_callback(self.async_write_ha_state)

    @property
    def device_info(self):
        """Return device information for the sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._controller.id)},
            name=self._controller.name,
            manufacturer=self._controller.manufacturer,
            model=self._controller.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the climate entity is available."""
        return self._controller.is_connected(self._installation_unique)

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
            controller,
            zone: Zone,
            installation_unique: str,
            entity_description: SensorEntityDescription,
    ):
        """Initialize the temperature sensor class."""
        super().__init__(controller, zone, installation_unique)
        self._attr_unique_id = f"{self._id}_temperature"
        self._attr_name = f"{self._name} Temperature"
        self.entity_description = entity_description

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._controller.get_temperature(self._zone_number)

class RehauNeasmart2OutdoorTemperatureSensor(SensorEntity, RestoreEntity):
    """Temperature sensor class for outdoor Rehau Neasmart."""

    device_class = TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    _attr_has_entity_name = True
    should_poll = False

    def __init__(self, controller: Controller, installation: Installation, propertyname: str, name: str, entity_description: SensorEntityDescription):
        """Initialize the generic sensor class."""
        self._installation = installation
        self._controller = controller
        self._available = True
        self._name = f"{name}"
        self._propertyname = propertyname
        self._installation_unique = installation.unique
        self._state = round((getattr(self._installation, propertyname) / 10 - 32) / 1.8, 1)
        self._unique_name = name.lower().replace(" ", "_")
        self._attr_unique_id = f"{self._installation_unique}_{self._unique_name}"
        self._attr_name = self._name
        self.entity_description = entity_description

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._controller.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Run when this Entity will be removed from HA."""
        self._controller.remove_callback(self.async_write_ha_state)

    @property
    def device_info(self):
        """Return device information for the sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._controller.id)},
            name=self._controller.name,
            manufacturer=self._controller.manufacturer,
            model=self._controller.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the climate entity is available."""
        return self._controller.is_connected(self._installation_unique)

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        installation = self._controller.get_installation_by_unique(self._installation_unique)
        return round((installation.get(self._propertyname) / 10 - 32) / 1.8, 1)

    @property
    def state(self):
        """Return the state of the sensor."""
        installation = self._controller.get_installation_by_unique(self._installation_unique)
        return round((installation.get(self._propertyname) / 10 - 32) / 1.8, 1)

