import base64
import json
import os
import uuid
import hashlib
from enum import Enum
from threading import Timer
import secrets


class OperationModes(Enum):
    HEATING_ONLY = 1
    COOLING_ONLY = 2
    AUTO = 3
    HEATING_MANUAL = 5
    COOLING_MANUAL = 6

class EnergyLevels(Enum):
    PRESENT_MODE = 0
    ABSENT_MODE = 1
    STANDBY_MODE = 2
    TIMING_MODE = 3
    PARTY_MODE = 7
    HOLIDAY_MODE = 11


def parse_operating_mode(heat_cool_auto: dict):
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


def get_global_energy_level(installation) -> EnergyLevels:
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


def generate_uuid() -> str:
    return str(uuid.uuid4())


async def sha256_hash(input_str):
    hash_object = hashlib.sha256()
    hash_object.update(input_str.encode())
    return hash_object.digest()


def base64_url_encode(buffer):
    return base64.urlsafe_b64encode(buffer).decode().rstrip("=")


async def convert_challenge(challenge):
    hash_result = await sha256_hash(challenge)
    result = base64_url_encode(hash_result)
    return result


async def generate_auth_url(client_id, scopes, redirect_uri, url, challenge):
    nonce = secrets.token_urlsafe(32)

    converted_challenge = await convert_challenge(challenge)
    e = (
        f"client_id={client_id}&"
        f"scope={scopes}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"nonce={nonce}&"
        f"code_challenge_method=S256&"
        f"code_challenge={converted_challenge}"
    )

    return f"{url}/authz-srv/authz?{e}"


def set_timeout(fn, ms, *args, **kwargs):
    t = Timer(ms / 1000., fn, args=args, kwargs=kwargs)
    t.start()
    return t

def get_by_value(value, referentials):
    return next((item for item in referentials if str(item['value']) == str(value)), None)


def replace_keys(input_object, referentials):
    if not isinstance(input_object, dict):
        return input_object

    for key in list(input_object.keys()):
        if isinstance(input_object[key], list):
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = [replace_keys(item, referentials) for item in input_object[key]]
                del input_object[key]
        elif isinstance(input_object[key], dict):
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = replace_keys(input_object[key], referentials)
                del input_object[key]
        else:
            if get_by_value(key, referentials):
                index = str(get_by_value(key, referentials)["index"])
                input_object[index] = input_object[key]
                del input_object[key]

    return input_object

def save_as_json(data, file_name):
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, file_name)

    with open(file_path, "w") as file:
        json.dump(data, file)

