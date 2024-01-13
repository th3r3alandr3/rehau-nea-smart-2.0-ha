"""Handlers for the refresh of the authentication token."""
import logging
import requests

from ..exceptions import MqttClientCommunicationError


_LOGGER = logging.getLogger(__name__)


def handle_refresh(refresh_token):
    """Handle the refresh of the authentication token.

    Args:
        refresh_token (str): The refresh token used to refresh the authentication token.

    Returns:
        dict: The response from the refresh API call.

    Raises:
        MqttClientCommunicationError: If there is an error while communicating with the MQTT client.
    """
    try:
        headers = {"Content-type": "application/json"}
        data = {"token": refresh_token}
        refresh_url = (
            "https://api.neasmart2.app.rehau.com/v2/api/authentication/refresh"
        )
        refreshInProcess = requests.post(refresh_url, json=data, headers=headers)

        response = refreshInProcess.json()

        return response

    except MqttClientCommunicationError as e:
        _LOGGER.error("Error while refreshing token: %s", e)
        return None
