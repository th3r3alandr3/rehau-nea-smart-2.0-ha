"""Enums for the Rehau NEA Smart 2 MQTT integration."""
from enum import Enum

class OperationModes(Enum):
    """Operation modes."""

    HEATING_ONLY = 1
    COOLING_ONLY = 2
    AUTO = 3
    HEATING_MANUAL = 5
    COOLING_MANUAL = 6


class EnergyLevels(Enum):
    """Energy levels."""

    PRESENT_MODE = 0
    ABSENT_MODE = 1
    STANDBY_MODE = 2
    TIMING_MODE = 3
    PARTY_MODE = 7
    HOLIDAY_MODE = 11
