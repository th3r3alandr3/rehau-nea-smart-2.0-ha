"""Constants for rehau_nea_smart_2."""
from logging import Logger, getLogger
from homeassistant.components.climate import (
    HVACMode,
)

from .mqtt import (
    EnergyLevels,
    OperationModes
)

LOGGER: Logger = getLogger(__package__)

NAME = "Rehua Nea Smart 2.0"
DOMAIN = "rehau_nea_smart_2"
VERSION = "0.1.0"
ATTRIBUTION = "Data provided by REHAU Nea Smart 2.0 Mqtt API"

PRESET_ENERGY_LEVELS_MAPPING = {
    "normal": EnergyLevels.PRESENT_MODE.value,
    "reduced": EnergyLevels.ABSENT_MODE.value,
    "standby": EnergyLevels.STANDBY_MODE.value,
    "auto": EnergyLevels.TIMING_MODE.value,
    "party": EnergyLevels.PARTY_MODE.value,
    "vacation": EnergyLevels.HOLIDAY_MODE.value,
}

PRESET_ENERGY_LEVELS_MAPPING_REVERSE = {
    v: k for k, v in PRESET_ENERGY_LEVELS_MAPPING.items()
}

custom_mappings = {4: "auto", 5: "auto", 6: "party"}
PRESET_ENERGY_LEVELS_MAPPING_REVERSE.update(custom_mappings)


PRESET_OPERATING_MODES_MAPPING = {
    "auto": OperationModes.AUTO.value,
    "heating": OperationModes.HEATING_ONLY.value,
    "cooling": OperationModes.COOLING_ONLY.value,
    "manual_heating": OperationModes.HEATING_MANUAL.value,
    "manual_cooling": OperationModes.COOLING_MANUAL.value,
}

PRESET_OPERATING_MODES_MAPPING_REVERSE = {
    v: k for k, v in PRESET_OPERATING_MODES_MAPPING.items()
}

PRESET_CLIMATE_MODES_MAPPING = {
    OperationModes.AUTO.value: HVACMode.AUTO,
    OperationModes.HEATING_ONLY.value: HVACMode.HEAT,
    OperationModes.COOLING_ONLY.value: HVACMode.COOL,
    OperationModes.HEATING_MANUAL.value: HVACMode.HEAT,
    OperationModes.COOLING_MANUAL.value: HVACMode.COOL,
}

PRESET_CLIMATE_MODES_MAPPING_REVERSE = {
    v: k
    for k, v in PRESET_CLIMATE_MODES_MAPPING.items()
    if k not in [OperationModes.HEATING_MANUAL, OperationModes.COOLING_MANUAL]
}
