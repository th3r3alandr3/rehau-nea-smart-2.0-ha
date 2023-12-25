"""Constants for integration_blueprint."""
from logging import Logger, getLogger
from homeassistant.components.climate import (
    HVACMode,
)

LOGGER: Logger = getLogger(__package__)

NAME = "Integration blueprint"
DOMAIN = "integration_blueprint"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

PRESET_STATES_MAPPING = {
    "Normal": "normal",
    "Reduced": "reduced",
    "Standby": "standby",
    "Party": "party",
}

PRESET_STATES_MAPPING_REVERSE = {v: k for k, v in PRESET_STATES_MAPPING.items()}

PRESET_CLIMATE_MODES_MAPPING = {
    "Heating": HVACMode.HEAT,
    "Cooling": HVACMode.COOL,
    "Heating and Cooling": HVACMode.AUTO,
    "Manual Heating": HVACMode.HEAT,
    "Manual Cooling": HVACMode.COOL,
}

PRESET_CLIMATE_MODES_MAPPING_REVERSE = {v: k for k, v in PRESET_CLIMATE_MODES_MAPPING.items() if k not in ["Manual Heating", "Manual Cooling"]}