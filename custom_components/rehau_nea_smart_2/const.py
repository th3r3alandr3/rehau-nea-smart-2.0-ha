"""Constants for rehau_nea_smart_2."""
from logging import Logger, getLogger
from homeassistant.components.climate import (
    HVACMode,
)

LOGGER: Logger = getLogger(__package__)

NAME = "Rehua Nea Smart 2.0"
DOMAIN = "rehau_nea_smart_2"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

PRESET_ENERGY_LEVELS_MAPPING = {
    "Normal": "normal",
    "Reduced": "reduced",
    "Standby": "standby",
    "Auto": "auto",
    "Vacation": "vacation",
}


PRESET_STATES_MAPPING = {
    "Normal": "normal",
    "Reduced": "reduced",
    "Standby": "standby",
    "Party": "party",
}

PRESET_STATES_MAPPING_REVERSE = {v: k for k, v in PRESET_STATES_MAPPING.items()}

PRESET_CLIMATE_MODES_MAPPING = {
    "Heating and Cooling": HVACMode.AUTO,
    "Heating": HVACMode.HEAT,
    "Cooling": HVACMode.COOL,
    "Manual Heating": HVACMode.HEAT,
    "Manual Cooling": HVACMode.COOL,
}

PRESET_CLIMATE_MODES_MAPPING_REVERSE = {
    v: k
    for k, v in PRESET_CLIMATE_MODES_MAPPING.items()
    if k not in ["Manual Heating", "Manual Cooling"]
}
