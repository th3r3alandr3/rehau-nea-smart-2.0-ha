"""MQTT client for the Rehau NEA Smart 2 integration."""
import asyncio
import json
import paho.mqtt.client as mqtt
import threading
import logging
import schedule
import time
import re

from .utils import generate_uuid, ServerTopics, ClientTopics, save_as_json, read_from_json
from .handlers import handle_message, auth, refresh, parse_installations, read_user_state
from .exceptions import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
    MqttClientError,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from deepmerge import Merger


_LOGGER = logging.getLogger(__name__)

class MqttClient:
    """MQTT client for the Rehau NEA Smart 2 integration."""
    MAX_CONNECT_RETRIES = 5

    def __init__(self, username, password):
        """Initialize the MQTT client.

        Args:
            username: The MQTT username.
            password: The MQTT password.
        """
        self.username = "app"
        self.password = "appuserplatform"
        self.auth_username = username
        self.auth_password = password
        self.token_data = None
        self.user = None
        self.installations = None
        self.authenticated = False
        self.referentials = None
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
        self.scheduler = AsyncIOScheduler()
        self.number_of_retries = 0

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
            self.number_of_retries += 1
            if self.number_of_retries <= self.MAX_CONNECT_RETRIES:
                _LOGGER.error("Unexpected disconnection. Retrying...")
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

    async def read_user(self):
        """Read user data from the server periodically."""
        _LOGGER.debug("Read user")
        payload = {
            "username": self.auth_username,
            "installs_ids": self.get_install_ids(),
            "install_hash": self.get_install_hash(),
            "token": self.token_data["access_token"],
            "demand": self.get_install_id(),
        }
        user = await read_user_state(payload)
        self.set_user(user)

    async def refresh(self):
        """Refresh the user data periodically."""
        _LOGGER.debug("Refreshing user data")
        self.number_of_retries = 0
        self.send_topics()
        await self.read_user()

    def replace_wildcards(self, topic: str):
        """Replace the wildcards in the topic with the installation ID and user mail.

        Args:
            string: The topic to replace the wildcards in.

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
            _LOGGER.error(f"Error sending message {topic}: {json_message}")

        return mid

    def start_mqtt_client(self):
        """Start the MQTT client's event loop."""
        self.client.loop_start()

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

    def init_mqtt_client(self):
        """Initialize the MQTT client."""
        _LOGGER.debug("Initializing MQTT client")
        if self.client:
            self.disconnect()
        self.client = mqtt.Client(client_id=self.client_id, transport="websockets")
        self.client.username_pw_set(self.username + "?x-amz-customauthorizer-name=app-front",
                                    self.token_data['access_token'])
        self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
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
        self.user = user
        self.set_install_id()
        self.set_installations(self.user["installs"])
        self.init_mqtt_client()

    async def refresh_token(self):
        """Refresh the authentication token."""

        _LOGGER.debug("Refreshing token")
        token_data = await refresh(self.token_data["refresh_token"])
        self.set_token_data(token_data)

    def set_installations(self, installations):
        """Set the installations.

        Args:
            installations: The installations.
        """
        if len(installations) > 0 and "groups" in installations[0] and len(installations[0]["groups"]) > 0:
            print("Writing installations to file")
            self.update_installations(installations)
            self.set_install_id()

    def update_installations(self, installations):
        """Write the installations to a file."""

        stored_installations = read_from_json("installations_raw.json")

        if stored_installations is not None and len(stored_installations) > 0:
            merger = Merger(
                [
                    (list, ["override"]),
                    (dict, ["merge"]),
                    (set, ["union"])
                ],
                ["override"],
                ["override"]
            )

            merged_installations = []
            for installation in installations:
                for stored_installation in stored_installations:
                    if installation["unique"] == stored_installation["unique"]:
                        merged_installations.append(merger.merge(stored_installation, installation))
                        break

        else:
            merged_installations = installations

        save_as_json(merged_installations, "installations_raw.json")

        _LOGGER.debug("Writing installations to file " + str(merged_installations))
        self.installations = parse_installations(merged_installations)

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

    def set_user(self, user):
        """Set the user data.

        Args:
            user: The user data.
        """
        self.user = user
        self.set_installations(user["installs"])

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
        return [install["_id"] for install in self.user["installs"]]

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

        _LOGGER.debug("Requesting referentials from server")
        payload = {
            "ID": self.auth_username,
            "data": {},
            "sso": True,
            "token": self.token_data["access_token"],
        }
        self.send_message(ServerTopics.USER_REFERENTIAL.value, payload)

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
                        return


        raise MqttClientError("No channel found for id " + channel_id)

    # def start_scheduler(self):
    #     """Start the scheduler to run periodic tasks."""
    #     _LOGGER.debug("Starting scheduler thread")
    #     schedule.every(60).seconds.do(self.refresh).tag("refresh")
    #     schedule.every(300).seconds.do(self.request_server_referentials).tag("referentials")
    #     if "access_token" in self.token_data:
    #         _LOGGER.debug("Scheduling token refresh")
    #         expires_in = self.token_data["expires_in"] - 300
    #         schedule.every(expires_in).seconds.do(self.refresh_token).tag("token")
    #     else:
    #         _LOGGER.error("No access token found")

    #     while not self.stop_scheduler_loop:
    #         schedule.run_pending(
    #         time.sleep(1)


    # def stop_scheduler(self):
    #     """Stop the scheduler."""
    #     _LOGGER.debug("Stopping scheduler")
    #     schedule.clear("refresh")
    #     schedule.clear("referentials")
    #     schedule.clear("token")
    #     self.stop_scheduler_loop = True

    # def start_scheduler_thread(self):
    #     """Start the scheduler in a separate thread."""
    #     self.scheduler_thread = threading.Thread(target=self.start_scheduler, name="Rehau NEA Smart 2 Scheduler")
    #     self.scheduler_thread.start()

    # def stop_scheduler_thread(self):
    #     """Stop the scheduler thread."""
    #     self.stop_scheduler()
    #     self.scheduler_thread.join()

    def start_scheduler(self):
        """Start the scheduler to run periodic tasks."""
        _LOGGER.debug("Starting scheduler thread")
        self.scheduler.add_job(self.refresh, 'interval', seconds=60, id="refresh")
        self.scheduler.add_job(self.request_server_referentials, 'interval', seconds=300, id="referentials")
        if "access_token" in self.token_data:
            _LOGGER.debug("Scheduling token refresh")
            expires_in = self.token_data["expires_in"] - 300
            self.scheduler.add_job(self.refresh_token, 'interval', seconds=expires_in, id="token")
        else:
            _LOGGER.error("No access token found")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.scheduler.start()

    def stop_scheduler(self):
        """Stop the scheduler."""
        _LOGGER.debug("Stopping scheduler")
        self.scheduler.remove_all_jobs()
        self.scheduler.shutdown()

