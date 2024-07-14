"""MQTT client for the Rehau NEA Smart 2 integration."""
import asyncio
import json
from collections.abc import Callable
import paho.mqtt.client as mqtt
import logging
import schedule
import aiocron
import time
import re

from .utils import generate_uuid, ServerTopics, ClientTopics
from .handlers import handle_message, auth, refresh, parse_installations, read_user_state
from .exceptions import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
    MqttClientError,
)
from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)

class MqttClient:
    """MQTT client for the Rehau NEA Smart 2 integration."""

    MAX_CONNECT_RETRIES = 5

    def __init__(self, hass: HomeAssistant, username, password):
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
        self.transaction_id = None
        self.last_operating_mode = None
        self.current_installation = {
            "id": None,
            "unique": None,
            "hash": None,
        }
        self.client_id = "app-" + generate_uuid()
        self.client = None
        self.subscribe_topics = lambda: [
            {"topic": ClientTopics.LISTEN.value, "options": {}},
            {"topic": ClientTopics.LISTEN_TO_CONTROLLER.value, "options": {}},
        ]
        self.stop_scheduler_loop = False
        self.scheduler_task = None
        self.number_of_retries = 0
        self.number_of_message_failures = 0
        self.callbacks = set()

    @staticmethod
    async def check_credentials(email, password):
        """Check if the provided credentials are valid.

        Args:
            email: The user's email.
            password: The user's password.
            hass: The Home Assistant instance.

        Returns:
            bool: True if the credentials are valid, False otherwise.

        Raises:
            MqttClientAuthenticationError: If the credentials are invalid.
        """
        valid = await auth(email, password, True)
        _LOGGER.debug("Credentials valid: " + str(valid))
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
        self.authenticated = True
        self.send_topics()
        self.request_server_referentials()

    async def on_message(self, client, userdata, msg):
        """Handle the received message.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            msg: The received message.
        """
        await handle_message(msg.topic, msg.payload, self)

    def on_disconnect(self, client, userdata, rc):
        """Log the result code when the client disconnects from the MQTT broker.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            rc: The result code.
        """
        if rc != 0:
            self.number_of_retries += 1
            if self.number_of_retries <= self.MAX_CONNECT_RETRIES:
                # A disconnect is expected every 10 minutes, so we don't want to log it as an error
                _LOGGER.info("Unexpected disconnection. Retrying...")
            else:
                _LOGGER.error("Unexpected disconnection. Stopping...")
                self.disconnect()

    def set_install_id(self):
        """Set the installation ID based on the user's default installation."""
        default_install = self.user["defaultInstall"]
        installs = self.user["installs"]
        for install in installs:
            if install["unique"] == default_install:
                self.current_installation = {
                    "id": install["_id"],
                    "unique": install["unique"],
                    "hash": install["hash"] if "hash" in install else None,
                }
                return

    async def read_user_http(self):
        """Read user data from the server periodically."""
        _LOGGER.debug("Read user")
        payload = {
            "username": self.auth_username,
            "installs_ids": self.get_install_ids(),
            "install_hash": self.get_install_hash(),
            "token": self.token_data["access_token"],
            "demand": self.get_install_id(),
        }
        try:
            user = await read_user_state(payload)
            if user is not None:
                await self.set_user(user)
        except MqttClientCommunicationError as e:
            _LOGGER.error("Error while refreshing user state: %s", e)
        except MqttClientAuthenticationError:
            _LOGGER.info("Token expired. Refreshing...")
            await self.refresh_token()

    async def refresh_http(self):
        """Refresh the user data periodically."""
        _LOGGER.debug("Refreshing user data")
        self.number_of_retries = 0
        self.send_topics()
        await self.read_user_http()

    def refresh(self):
        """Refresh the user data periodically."""
        _LOGGER.debug("Refreshing user data")
        self.number_of_retries = 0
        self.send_topics()
        self.read_user()

    def read_user(self):
        """Read user data from the server."""
        _LOGGER.debug("Read user")
        payload = {
            "ID": self.auth_username,
            "token": self.token_data["access_token"],
            "sso": True,
            "data": {
                "demand": self.get_install_id(),
                "email": self.auth_username,
            },
        }
        self.send_message(ServerTopics.USER_READ.value, payload)

    def replace_wildcards(self, topic: str):
        """Replace the wildcards in the topic with the installation ID and user mail.

        Args:
            topic: The topic to replace the wildcards in.

        Returns:
            str: The topic with the wildcards replaced.
        """
        replacements = {
            "{id}": self.get_install_unique(),
            "{email}": self.auth_username,
        }

        def replace(match):
            return replacements[match.group(0)]

        return re.sub(r"{id}|{email}", replace, topic, flags=re.I)

    def send_topics(self):
        """Subscribe to the configured topics."""
        for topic in self.subscribe_topics():
            topic_str = self.replace_wildcards(topic["topic"])
            _LOGGER.debug(f"Subscribing to topic: {topic_str}")
            self.client.unsubscribe(topic_str)
            self.client.subscribe(topic_str, **topic["options"])

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
        topic = self.replace_wildcards(topic)
        _LOGGER.debug(f"Sending message {topic}: {json_message}")
        result, mid = self.client.publish(topic, payload=json_message)
        if result != mqtt.MQTT_ERR_SUCCESS:
            self.number_of_message_failures += 1
            if self.number_of_message_failures > 5:
                _LOGGER.error(f"Error sending message {topic}. Failed {self.number_of_message_failures} times. Data: {json_message}")
        else:
            self.number_of_message_failures = 0
        return mid

    def start_mqtt_client(self):
        """Start the MQTT client's event loop."""
        self.client.loop_start()

    async def reconnect(self):
        """Reconnect to the MQTT broker."""
        await self.init_mqtt_client()

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        for topic in self.subscribe_topics():
            topic_str = self.replace_wildcards(topic["topic"])
            _LOGGER.debug(f"Unsubscribing from topic: {topic_str}")
            self.client.unsubscribe(topic_str)
        self.client.disconnect()
        self.client.loop_stop()
        self.stop_scheduler()
        _LOGGER.debug("Disconnected")


    def on_message_callback(self, client, userdata, message):
        """Handle the received message in a separate task.

        Args:
            client: The MQTT client instance.
            userdata: The user data.
            msg: The received message.
        """
        self.hass.create_task(self.on_message(client, userdata, message))

    async def init_mqtt_client(self):
        """Initialize the MQTT client."""
        _LOGGER.debug("Initializing MQTT client")
        if self.client:
            self.disconnect()
        self.client = mqtt.Client(client_id=self.client_id, transport="websockets")
        self.client.username_pw_set(self.username + "?x-amz-customauthorizer-name=app-front",
                                    self.token_data['access_token'])
        self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message_callback
        self.client.on_disconnect = self.on_disconnect
        self.client.enable_logger(logger=_LOGGER)
        self.client.reconnect_delay_set(min_delay=30, max_delay=300)
        self.client.connect("mqtt.nea2aws.aws.rehau.cloud", 443)
        self.start_scheduler()
        self.start_mqtt_client()

    async def auth_user(self):
        """Authenticate the user with the provided credentials."""
        token_data, user = await auth(self.auth_username, self.auth_password)
        self.set_token_data(token_data)
        await self.set_user(user)
        await self.init_mqtt_client()

    async def refresh_token(self):
        """Refresh the authentication token."""

        _LOGGER.debug("Refreshing token")
        try:
            token_data = await refresh(self.token_data["refresh_token"])
            self.set_token_data(token_data)
            await self.reconnect()
        except MqttClientAuthenticationError as e:
            _LOGGER.error("Could not refresh token: " + str(e))
            await self.auth_user()

    async def set_installations(self, installations):
        """Set the installations.

        Args:
            installations: The installations.
        """
        if len(installations) > 0 and "groups" in installations[0] and len(installations[0]["groups"]) > 0:
            await self.update_installations(installations)
            self.set_install_id()

    async def update_installations(self, installations):
        """Write the installations to a file."""
        self.installations = parse_installations(installations, self.last_operating_mode)
        await self.publish_updates()

    def set_token_data(self, token_data):
        """Set the authentication token data and start the refresh timer.

        Args:
            token_data: The token data.
        """
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

    def get_transaction_id(self):
        """Get the transaction ID.

        Returns:
            str: The transaction ID.
        """
        if self.transaction_id is not None:
            return self.transaction_id

        self.transaction_id = self.user["transactionId"] if "transactionId" in self.user else None
        return self.transaction_id

    async def set_user(self, user):
        """Set the user data.

        Args:
            user: The user data.
        """
        self.user = user
        if "installs" in user:
            if len(user["installs"]) > 0 and "user" in user["installs"][0] and "heatcool_auto_01" in user["installs"][0]["user"]:
                self.last_operating_mode = user["installs"][0]["user"]["heatcool_auto_01"]
                _LOGGER.debug("Setting last operating mode to " + str(self.last_operating_mode))
            await self.set_installations(user["installs"])

    def get_install_id(self):
        """Get the installation ID.

        Returns:
            str: The installation ID.
        """
        return self.current_installation["id"]

    def get_install_unique(self):
        """Get the installation unique.

        Returns:
            str: The installation unique.
        """
        return self.current_installation["unique"]

    def get_install_hash(self):
        """Get the installation hash.

        Returns:
            str: The installation hash.
        """
        return self.current_installation["hash"]

    def get_install_ids(self):
        """Get the installation IDs.

        Returns:
            list: The installation IDs.
        """
        return [install["id"] for install in self.get_installations()]

    def get_referentials(self):
        """Get the referentials.

        Returns:
            list: The referentials.
        """
        if self.referentials is not None:
            return self.referentials
        else:
            raise MqttClientError("No referentials found")

    def request_server_referentials(self):
        """Request the referentials from the server."""

        _LOGGER.debug("Requesting referentials from server")
        payload = {
            "ID": self.auth_username,
            "data": {},
            "sso": True,
            "token": self.token_data["access_token"],
        }
        self.send_message(ServerTopics.USER_REFERENTIAL.value, payload)

    async def update_channel(self, payload: dict):
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
                if installation["unique"] == install_id
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
                        await self.publish_updates()
                        return


        raise MqttClientError("No channel found for id " + channel_id)


    async def publish_updates(self) -> None:
        """Publish updates to all registered callbacks."""
        for callback in self.callbacks:
            callback()


    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state.

        Args:
            callback (Callable[[], None]): Callback to be called when Roller changes state.
        """
        self.callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback.

        Args:
            callback (Callable[[], None]): Callback to be removed.
        """
        self.callbacks.discard(callback)

    def run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while not self.stop_scheduler_loop:
            schedule.run_pending()
            time.sleep(1)

    async def start_scheduler_task(self):
        """Start the scheduler in a separate thread."""
        _LOGGER.debug("Starting scheduler thread")
        aiocron.crontab("*/1 * * * *", func=self.refresh_http, start=True)
        aiocron.crontab("*/5 * * * *", func=self.request_server_referentials, start=True)
        if "access_token" in self.token_data:
            _LOGGER.debug("Scheduling token refresh")
            expires_in = self.token_data["expires_in"] - 300
            _LOGGER.debug("Token expires in " + str(expires_in) + " seconds")
            # aiocron.crontab(f"*/{expires_in} * * * *", func=self.refresh_token, start=True)
        else:
            _LOGGER.error("No access token found")

        while not self.stop_scheduler_loop:
            await asyncio.sleep(1)

    def start_scheduler(self):
        """Start the scheduler to run periodic tasks."""
        self.scheduler_task = asyncio.create_task(self.start_scheduler_task(), name="Rehau NEA Smart 2 Scheduler")

    def stop_scheduler(self):
        """Stop the scheduler."""
        _LOGGER.debug("Stopping scheduler")
        self.stop_scheduler_loop = True
        if self.scheduler_task:
            self.scheduler_task.cancel()
            self.scheduler_task = None


