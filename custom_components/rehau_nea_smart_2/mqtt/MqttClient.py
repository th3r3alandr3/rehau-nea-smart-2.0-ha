"""MQTT client for the Rehau NEA Smart 2 integration."""

import json
import paho.mqtt.client as mqtt
import threading
import logging

from .utils import generate_uuid
from .handlers import handle_message, auth, handle_refresh
from .exceptions import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
    MqttClientError,
)

_LOGGER = logging.getLogger(__name__)


class MqttClient:
    """MQTT client for the Rehau NEA Smart 2 integration."""

    def __init__(self, hass, username, password):
        """Initialize the MQTT client.

        Args:
            hass: The Home Assistant instance.
            username: The MQTT username.
            password: The MQTT password.
        """
        self.hass = hass
        self.username = "app"
        self.password = "appuserplatform"
        self.auth_username = username
        self.auth_password = password
        self.token_data = None
        self.user = None
        self.installations = None
        self.authenticated = False
        self.referentials = None
        self.install_id = None
        self.client_id = "app"
        self.client = None
        self.topics = [{"topic": "$client/app", "options": {}}]
        self.refresh_in_process = False
        self.init_mqtt_client()

    async def check_credentials(self, email, password):
        """Check if the provided credentials are valid.

        Args:
            email: The user's email.
            password: The user's password.

        Returns:
            bool: True if the credentials are valid, False otherwise.

        Raises:
            MqttClientAuthenticationError: If the credentials are invalid.
        """
        valid = await auth(self.hass, email, password, True)
        if valid:
            return True

        raise MqttClientAuthenticationError("Invalid credentials")

    def is_authenticated(self):
        """Check if the MQTT client is authenticated.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        return self.authenticated

    def is_ready(self):
        """Check if the MQTT client is ready.

        Returns:
            bool: True if ready, False otherwise.
        """
        return self.user is not None and self.installations is not None

    def on_connect(self, client, userdata, flags, rc):
        """Log the result code when the client connects to the MQTT broker.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            flags: The connection flags.
            rc: The result code.
        """
        _LOGGER.debug("Connected with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        """Handle the received message.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            msg: The received message.
        """
        handle_message(msg.topic, msg.payload, self)

    def on_disconnect(self, client, userdata, rc):
        """Log the result code when the client disconnects from the MQTT broker.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            rc: The result code.
        """
        if rc != 0:
            _LOGGER.error("Unexpected disconnection.")

    def set_install_id(self):
        """Set the installation ID based on the user's default installation."""
        default_install = self.user["defaultInstall"]
        installs = self.user["installs"]
        for install in installs:
            if install["unique"] == default_install:
                self.install_id = install["_id"]
                return

    def read_user(self):
        """Read user data from the server periodically."""
        _LOGGER.debug("Read user")
        payload = {
            "clientid": self.client_id,
            "sso": True,
            "token": self.token_data["access_token"],
            "data": {"demand": self.install_id if self.install_id else "default"},
        }
        self.send_message("@server/user/read", payload)
        self.refresh_in_process = False

    def refresh(self):
        """Refresh the user data periodically."""
        if self.refresh_in_process:
            return

        self.refresh_in_process = True
        self.send_topics()
        self.read_user()
        threading.Timer(60, self.refresh).start()

    def send_topics(self):
        """Subscribe to the configured topics."""
        for topic in self.topics:
            _LOGGER.debug(f"Subscribing to topic: {topic['topic']}")
            self.client.unsubscribe(topic["topic"])
            self.client.subscribe(topic["topic"], **topic["options"])

    def send_message(self, topic: str, message: dict):
        """Send a message to the MQTT broker.

        Args:
            topic: The topic to publish the message to.
            message: The message to send.

        Returns:
            int: The message ID.

        Raises:
            MqttClientCommunicationError: If there is a communication error.
        """
        json_message = json.dumps(message)
        _LOGGER.debug(f"Sending message {topic}: {json_message}")
        result, mid = self.client.publish(topic, payload=json_message)
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise MqttClientCommunicationError("Failed to send message")

        return mid

    def start_mqtt_client(self):
        """Start the MQTT client's event loop."""
        self.client.loop_start()

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        for topic in self.topics:
            _LOGGER.debug(f"Unsubscribing from topic: {topic['topic']}")
            self.client.unsubscribe(topic["topic"])
        self.client.disconnect()
        self.client.loop_stop()
        _LOGGER.debug("Disconnected")

    def init_mqtt_client(self):
        """Initialize the MQTT client."""
        if self.client:
            self.disconnect()

        self.client = mqtt.Client(client_id=self.client_id, transport="websockets")
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.connect("iot.neasmart2.app.rehau.com", 8094)
        self.send_topics()
        self.start_mqtt_client()

    def user_auth(self):
        """Authenticate the user with the server."""
        _LOGGER.debug("User auth")
        payload = {
            "clientid": self.client_id,
            "token": self.token_data["access_token"],
            "sso": True,
            "data": {"transactionId": generate_uuid()},
        }
        self.send_message("@server/user/auth", payload)

    async def auth_user(self):
        """Authenticate the user with the provided credentials."""
        token_data = await auth(self.hass, self.auth_username, self.auth_password)
        self.set_token_data(token_data)
        self.user_auth()

    def refresh_token(self):
        """Refresh the authentication token."""
        refresh_token = self.token_data["refresh_token"]
        token_data = handle_refresh(refresh_token)
        if token_data is not None:
            self.set_token_data(token_data)
        else:
            self.auth_user()

    def refresh_timer(self, expires_in):
        """Start a timer to refresh the authentication token.

        Args:
            expires_in: The number of seconds until the token expires.
        """
        _LOGGER.debug("Refreshing token in " + str(expires_in) + " seconds")
        threading.Timer(expires_in, self.refresh_token).start()

    def set_token_data(self, token_data):
        """Set the authentication token data and start the refresh timer.

        Args:
            token_data: The token data.
        """
        expires_in = token_data["expires_in"] - 60
        threading.Thread(target=self.refresh_timer, args=(expires_in,)).start()
        self.token_data = token_data

    def get_installations(self):
        """Get the list of installations.

        Returns:
            list: The list of installations.
        """
        return self.installations

    def get_user(self):
        """Get the user data.

        Returns:
            dict: The user data.
        """
        return self.user

    def get_install_id(self):
        """Get the installation ID.

        Returns:
            str: The installation ID.
        """
        return self.install_id

    def get_referentials(self):
        """Get the referentials.

        Returns:
            list: The referentials.
        """
        if self.referentials is not None:
            return self.referentials
        else:
            with open("./data/referentials.json") as referentials_file:
                self.referentials = json.load(referentials_file)["referentials"]
                return self.referentials

    def request_server_referentials(self):
        """Request the referentials from the server."""
        payload = {
            "clientid": self.client_id,
            "data": {},
            "sso": True,
            "token": self.token_data["access_token"],
        }
        self.send_message("@server/user/referential", payload)

    def update_channel(self, payload: dict):
        """Update the channel with the provided payload.

        Args:
            payload: The payload containing the channel ID, installation ID, mode used, and setpoint used.

        Raises:
            MqttClientError: If the channel or installation is not found.
        """
        channel_id = payload["channel_id"]
        install_id = payload["install_id"]
        mode_used = payload["mode_used"]
        setpoint_used = payload["setpoint_used"]

        installation = next(
            (
                installation
                for installation in self.installations
                if installation["id"] == install_id
            ),
            None,
        )
        if installation is None:
            raise MqttClientError("No installation found for id " + install_id)

        for group in installation["groups"]:
            for zone in group["zones"]:
                for channel in zone["channels"]:
                    if channel["id"] == channel_id:
                        channel["energy_level"] = mode_used
                        channel["target_temperature"] = setpoint_used
                        return

        raise MqttClientError("No channel found for id " + channel_id)
