"""Helper functions for parsing operating modes."""
from .enums import OperationModes


def parse_operating_mode(heat_cool_auto: dict):
    """Parse the operating mode based on the provided heat_cool_auto dictionary.

    Args:
        heat_cool_auto (dict): A dictionary containing the heating, cooling, and manual flags.

    Returns:
        int: The corresponding OperationModes value representing the operating mode.
    """
    if heat_cool_auto is None or not isinstance(heat_cool_auto, dict) or "heating" not in heat_cool_auto or "cooling" not in heat_cool_auto or "manual" not in heat_cool_auto:
        return OperationModes.UNKNOWN.value

    if heat_cool_auto["heating"] and heat_cool_auto["cooling"]:
        return OperationModes.AUTO.value
    elif heat_cool_auto["cooling"]:
        if heat_cool_auto["manual"]:
            return OperationModes.COOLING_MANUAL.value
        else:
            return OperationModes.COOLING_ONLY.value
    else:
        if heat_cool_auto["manual"]:
            return OperationModes.HEATING_MANUAL.value
        else:
            return OperationModes.HEATING_ONLY.value
