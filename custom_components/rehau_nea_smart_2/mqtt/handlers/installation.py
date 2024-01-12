"""Handlers for installation data."""
from ..models import Installation
from ..utils import parse_operating_mode, get_global_energy_level, save_as_json


def parse_installations(installations) -> list[Installation]:
    """Parse installations data."""
    installations_data = [
        {
            "id": installation["_id"],
            "unique": installation["unique"],
            "global_energy_level": get_global_energy_level(installation).value,
            "operating_mode": parse_operating_mode(
                installation["user"]["heatcool_auto_01"]
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
                                    "target_temperature": channel["setpoint_used"],
                                    "current_temperature": channel["temp_zone"],
                                    "energy_level": channel["mode_permanent"],
                                    "operating_mode": parse_operating_mode(
                                        installation["user"]["heatcool_auto_01"]
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

    save_as_json(installations_data, "installations.json")

    return installations_data
