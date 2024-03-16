"""The Rehau Nea Smart 2 MQTT handlers."""

from .auth import auth, refresh
from .installation import parse_installations, update_temperature, update_energy_level, update_operating_mode
from .message import handle_message
from .user import read_user_state

def __init__():
    """Initialize the Rehau Nea Smart 2 MQTT handlers."""
    pass
