"""Helper functions for calculating the global energy level of an installation."""
from .enums import EnergyLevels

def get_global_energy_level(installation) -> EnergyLevels:
    """Calculate the global energy level based on the provided installation dictionary.

    Args:
        installation (dict): A dictionary representing the installation.

    Returns:
        EnergyLevels: The maximum EnergyLevels value representing the global energy level.
    """
    mode_count = {
        EnergyLevels.PRESENT_MODE.value: 0,
        EnergyLevels.ABSENT_MODE.value: 0,
        EnergyLevels.STANDBY_MODE.value: 0,
        EnergyLevels.TIMING_MODE.value: 0,
        EnergyLevels.PARTY_MODE.value: 0,
        EnergyLevels.HOLIDAY_MODE.value: 0,
    }

    for group in installation["groups"]:
        for zone in group["zones"]:
            for channel in zone["channels"]:
                if channel["mode_permanent"] == EnergyLevels.PRESENT_MODE.value:
                    mode_count[EnergyLevels.PRESENT_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.ABSENT_MODE.value:
                    mode_count[EnergyLevels.ABSENT_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.STANDBY_MODE.value:
                    mode_count[EnergyLevels.STANDBY_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.TIMING_MODE.value:
                    mode_count[EnergyLevels.TIMING_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.PARTY_MODE.value:
                    mode_count[EnergyLevels.PARTY_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.HOLIDAY_MODE.value:
                    mode_count[EnergyLevels.HOLIDAY_MODE.value] += 1

    return EnergyLevels(max(mode_count, key=mode_count.get))
