"""Handlers for MQTT messages."""
import json
import logging

from ..utils import save_as_json, decompress_utf16
from .installation import parse_installations
import base64

_LOGGER = logging.getLogger(__name__)


def handle_message(topic: str, payload: str, client):
    """Handle MQTT message."""
    _LOGGER.debug("Handling message: " + topic)
    if topic == "$client/app":
        handle_app_message(payload, client)
    else:
        handle_user_message(payload, client)


def handle_app_message(payload: str, client):
    """Handle app message."""
    message = json.loads(payload)
    _LOGGER.debug("Handling app message: " + message["type"])
    if message["type"] == "auth_user":
        handle_user_auth(message, client)
    else:
        _LOGGER.debug("Unhandled app message: " + message["type"])


def handle_user_message(payload: str, client):
    """Handle user message."""
    message = json.loads(payload)
    _LOGGER.debug("Handling user message: " + message["type"])
    if message["type"] == "read_user":
        handle_user_read(message, client)
    elif message["type"] == "channel_update":
        handle_channel_update(message, client)
    elif message["type"] == "referential":
        handle_referential(message, client)
    else:
        _LOGGER.debug("Unhandled user message: " + message["type"])


def handle_user_read(message: dict, client):
    """Handle user read."""
    _LOGGER.debug("Handling user read")
    data = decompress_utf16(message["data"])
    _LOGGER.debug("User data: " + str(data))
    client.set_user(data)


def handle_user_auth(message: dict, client):
    """Handle user auth."""
    data = decompress_utf16(message["data"])
    client.user = data["user"]
    client.set_install_id()
    encoded = base64.b64encode(client.user["_id"].encode("utf-8"))
    client.password = encoded.decode("utf-8")
    client.username = client.user["username"]
    client.client_id = client.username

    client.topics = [{
        "topic": "$client/" + client.username,
        "options": {}
    }]
    client.init_mqtt_client()
    client.authenticated = True
    client.request_server_referentials()
    client.refresh()
    client.start_scheduler_thread()


def handle_channel_update(message, client):
    """Handle channel update."""
    channel_id = message["data"]["channel"]
    unique = message["data"]["unique"]
    data = message["data"]["data"]
    mode_used = data["mode_used"]
    setpoint_used = data["setpoint_used"]
    _LOGGER.debug(f"Channel {channel_id} updated to {mode_used} {setpoint_used}")
    client.update_channel({
        "channel_id": channel_id,
        "install_id": unique,
        "mode_used": mode_used,
        "setpoint_used": setpoint_used
    })


def handle_referential(message, client):
    """Handle referential."""
    referentials = decompress_utf16(message["data"])
    client.referentials = referentials
    save_as_json(referentials, "referentials.json")
    _LOGGER.debug("Referentials updated")
