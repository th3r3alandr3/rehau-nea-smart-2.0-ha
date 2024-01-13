"""The Rehau Nea Smart 2 MQTT handlers."""

from .auth import auth
from .installation import parse_installations, update_temperature, update_energy_level, update_operating_mode
from .message import handle_message
from .refresh import handle_refresh

def __init__():
    """Initialize the Rehau Nea Smart 2 MQTT handlers."""
    pass
