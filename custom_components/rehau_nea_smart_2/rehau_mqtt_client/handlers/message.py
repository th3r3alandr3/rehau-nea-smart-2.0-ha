"""Handlers for MQTT messages."""
import json
import logging

from ..utils import decompress_utf16

_LOGGER = logging.getLogger(__name__)


async def handle_message(topic: str, payload: str, client):
    """Handle MQTT message."""
    _LOGGER.debug("Handling message: " + topic)
    if topic == "$client/app":
        await handle_app_message(payload, client)
    else:
        await handle_user_message(payload, client)


async def handle_app_message(payload: str, client):
    """Handle app message."""
    message = json.loads(payload)
    _LOGGER.debug("Handling app message: " + message["type"])
    if message["type"] == "auth_user":
        await handle_user_auth(message, client)
    else:
        _LOGGER.debug("Unhandled app message: " + message["type"])


async def handle_user_message(payload: str, client):
    """Handle user message."""
    message = json.loads(payload)
    _LOGGER.debug("Handling user message: " + message["type"])
    if message["type"] == "read_user":
        await handle_user_read(message, client)
    elif message["type"] == "channel_update":
        await handle_channel_update(message, client)
    elif message["type"] == "referential":
        await handle_referential(message, client)
    else:
        _LOGGER.debug("Unhandled user message: " + message["type"])


async def handle_user_read(message: dict, client):
    """Handle user read."""
    raise NotImplementedError("handle_user_read is deprecated")


async def handle_user_auth(message: dict, client):
    """Handle user auth."""
    raise NotImplementedError("handle_user_auth is deprecated")


async def handle_channel_update(message, client):
    """Handle channel update."""
    channel_id = message["data"]["channel"]
    unique = message["data"]["unique"]
    data = message["data"]["data"]
    mode_used = data["mode_used"]
    setpoint_used = data["setpoint_used"]
    _LOGGER.debug(f"Channel {channel_id} updated to {mode_used} {setpoint_used}")
    await client.update_channel({
        "channel_id": channel_id,
        "install_id": unique,
        "mode_used": mode_used,
        "setpoint_used": setpoint_used
    })


async def handle_referential(message, client):
    """Handle referential."""
    referentials = decompress_utf16(message["data"])
    client.referentials = referentials
    _LOGGER.debug("Referentials updated")
