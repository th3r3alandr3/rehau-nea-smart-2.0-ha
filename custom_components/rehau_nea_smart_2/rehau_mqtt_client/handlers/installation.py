"""Handlers for installation data."""
from ..models import Installation
from ..utils import parse_operating_mode, get_global_energy_level, save_as_json
import datetime

def is_installation_connected(installation) -> bool:
    """Check if installation is connected."""
    if 'lastConnection' in installation and 'connectionState' in installation:
        last_connection = installation['lastConnection']
        connection_state = installation['connectionState']

        last_connection_date = datetime.datetime.strptime(last_connection, '%Y-%m-%dT%H:%M:%S.%fZ')

        return connection_state and last_connection_date is not None

    return False

def parse_installations(installations, last_operation_mode) -> list[Installation]:
    """Parse installations data."""

    installations_data = [
        {
            "id": installation["_id"],
            "connected": is_installation_connected(installation),
            "unique": installation["unique"],
            "outside_temp": installation["outside_temp"],
            "outsideTempFiltered": installation["outsideTempFiltered"],
            "hash": installation["hash"] if "hash" in installation else None,
            "global_energy_level": get_global_energy_level(installation).value,
            "operating_mode": parse_operating_mode(
                installation["user"]["heatcool_auto_01"] if "user" in installation else last_operation_mode
            ),
            "groups": [
                {
                    "id": group["_id"],
                    "group_name": group["name"],
                    "zones": [
                        {
                            "id": zone["_id"],
                            "name": zone["name"],
                            "number": zone["number"],
                            "channels": [
                                {
                                    "id": channel["_id"],
                                    "humidity": channel["humidity"],
                                    "target_temperature": channel["setpoint_used"],
                                    "current_temperature": channel["temp_zone"],
                                    "energy_level": channel["mode_permanent"],
                                    "operating_mode": parse_operating_mode(
                                        installation["user"]["heatcool_auto_01"] if "user" in installation else last_operation_mode
                                    ),
                                    "setpoints": {
                                        "cooling": {
                                            "normal": channel["setpoint_c_normal"],
                                            "reduced": channel["setpoint_c_reduced"],
                                        },
                                        "heating": {
                                            "normal": channel["setpoint_h_normal"],
                                            "reduced": channel["setpoint_h_reduced"],
                                            "standby": channel["setpoint_h_standby"],
                                        },
                                        "min": channel["setpoint_min"],
                                        "max": channel["setpoint_max"],
                                    },
                                }
                                for channel in zone["channels"]
                            ],
                        }
                        for zone in group["zones"]
                    ],
                }
                for group in installation["groups"]
            ],
        }
        for installation in installations
    ]

    return installations_data


def update_temperature(installations: list[Installation], zone_number: str, temperature: float) -> list[Installation]:
    """Update temperature."""
    for installation in installations:
        for group in installation["groups"]:
            for zone in group["zones"]:
                if zone["number"] == zone_number:
                    for channel in zone["channels"]:
                        channel["target_temperature"] = temperature

    return installations

def update_energy_level(installations: list[Installation], zone_number: str, energy_level: int) -> list[Installation]:
    """Update energy level."""
    for installation in installations:
        for group in installation["groups"]:
            for zone in group["zones"]:
                if zone["number"] == zone_number:
                    for channel in zone["channels"]:
                        channel["energy_level"] = energy_level

    return installations

def update_operating_mode(installations: list[Installation], unique: str, operating_mode: str) -> list[Installation]:
    """Update operating mode."""
    for installation in installations:
        if installation["unique"] == unique:
            installation["operating_mode"] = operating_mode
        for group in installation["groups"]:
            for zone in group["zones"]:
                for channel in zone["channels"]:
                    channel["operating_mode"] = operating_mode

    return installations
