"""The MQTT Utils package."""

from .enums import OperationModes, EnergyLevels, ServerTopics, ClientTopics
from .operating_modes import parse_operating_mode
from .energy_levels import get_global_energy_level
from .uuid_generator import generate_uuid
from .hashing import sha256_hash, base64_url_encode, convert_challenge
from .auth_url_generator import generate_auth_url
from .referentials import get_by_value, replace_keys
from .file_handler import save_as_json, read_from_json
from .decompress import decompress_utf16, decode_base64, encode_base64


def __init__():
    """Initialize the MQTT Utils package."""
    pass
