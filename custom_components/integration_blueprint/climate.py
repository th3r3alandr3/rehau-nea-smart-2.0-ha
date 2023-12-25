import logging

from custom_components.integration_blueprint.coordinator import (
    RehauNeaSmart2DataUpdateCoordinator,
)
from .const import (
    DOMAIN,
    PRESET_STATES_MAPPING,
    PRESET_STATES_MAPPING_REVERSE,
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
        key="integration_blueprint",
        name="Integration Climate",
        icon="mdi:home-thermometer",
        translation_key="rehauneasmart2"
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the climate platform."""
    coordinator: RehauNeaSmart2DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    rooms = await coordinator.async_get_rooms_detailed()
    settings = await coordinator.async_get_settings()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        for room in rooms:
            room["operation_mode"] = settings["operation_mode"]
            devices.append(
                RehauNeaSmart2RoomClimate(coordinator, room, entity_description)
            )

    async_add_devices(devices)


class IntegrationRehauNeaSmart2Climate(ClimateEntity, RestoreEntity):
    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: RehauNeaSmart2DataUpdateCoordinator, room):
        self._coordinator = coordinator
        self._state = None
        self._available = True
        self._id = room["id"]
        self._room_name = room["room_name"]
        self._current_temp = room["current_temp"]
        self._target_temp = room["target_temp"]
        self._mode = room["mode"]
        self._max_temp = room["max_temp"]
        self._min_temp = room["min_temp"]
        self._week_program = room["week_program"]
        self._operation_mode = room["operation_mode"]

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.id)},
            name=self._coordinator.name,
            manufacturer=self._coordinator.manufacturer,
            model=self._coordinator.model,
        )

    @property
    def available(self) -> bool:
        return True


class RehauNeaSmart2RoomClimate(IntegrationRehauNeaSmart2Climate):
    def __init__(
        self,
        coordinator: RehauNeaSmart2DataUpdateCoordinator,
        room,
        entity_description: ClimateEntityDescription,
    ):
        super().__init__(coordinator, room)
        self._attr_unique_id = f"{self._id}_thermostat"
        self._attr_name = f"{self._room_name} Thermostat"
        self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.COOL]
        self._attr_preset_modes = list(PRESET_STATES_MAPPING.keys())
        self.entity_description = entity_description

        self._attr_preset_mode = PRESET_STATES_MAPPING_REVERSE[self._mode]
        self._attr_hvac_mode = PRESET_CLIMATE_MODES_MAPPING[self._operation_mode]
        self._attr_current_temperature = self._current_temp
        self._attr_target_temperature = self._target_temp
        self._attr_max_temp = self._max_temp
        self._attr_min_temp = self._min_temp

    async def async_update(self) -> None:
        room = await self._coordinator.get_room(self._id)
        if (
            room is not None
            and room["mode"] is not None
            and room["current_temp"] is not None
            and room["target_temp"] is not None
        ):
            self._attr_preset_mode = PRESET_STATES_MAPPING_REVERSE[room["mode"]]
            self._attr_current_temperature = room["current_temp"]
            self._attr_target_temperature = room["target_temp"]
        else:
            _LOGGER.error(f"Error updating {self._attr_unique_id} thermostat")

    async def async_set_preset_mode(self, preset_mode: str):
        mode = PRESET_STATES_MAPPING[preset_mode]
        self._attr_preset_mode = preset_mode
        room = {"id": self._id, "mode": mode, "target_temp": self._attr_target_temperature}
        if not await self._coordinator.async_set_room(room):
            _LOGGER.error(
                f"Error setting mode for {self._attr_unique_id} thermostat"
            )

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        mode = PRESET_STATES_MAPPING[self._attr_preset_mode]
        # self._attr_target_temperature = temperature
        room = {"id": self._id, "mode": mode, "target_temp": temperature}
        if not await self._coordinator.async_set_room(room):
            _LOGGER.error(
                f"Error setting temperature for {self._attr_unique_id} thermostat"
            )

    async def async_set_hvac_mode(self, hvac_mode: str):
        operation_mode = PRESET_CLIMATE_MODES_MAPPING_REVERSE[hvac_mode]
        self._attr_hvac_mode = hvac_mode
        return True
