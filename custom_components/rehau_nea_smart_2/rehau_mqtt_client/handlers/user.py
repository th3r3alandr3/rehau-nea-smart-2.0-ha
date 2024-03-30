"""Handlers for the refresh of the authentication token."""
import logging
import httpx

from ..exceptions import MqttClientCommunicationError, MqttClientAuthenticationError


_LOGGER = logging.getLogger(__name__)


async def read_user_state(payload: dict):
    """Handle the refresh of the authentication token.

    Args:
        payload: The payload to send to the API.

    Returns:
        dict: The response from the refresh API call.

    Raises:
        MqttClientCommunicationError: If there is an error while communicating with the MQTT client.
    """
    url = f"https://api.nea2aws.aws.rehau.cloud/v1/users/{payload['username']}/getDataofInstall?demand={payload['demand']}&installsList={payload['installs_ids']}&hash={payload['install_hash']}"
    headers = {"Authorization": payload['token']}
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(url, headers=headers, timeout=60)
            if user_response.status_code >= 400:
                if user_response.status_code == 401:
                    raise MqttClientAuthenticationError("Could not read user data from the API. Status code: " + str(user_response.status_code) + " Reason: " + user_response.text)
                else:
                    raise MqttClientCommunicationError("Could not read user data from the API. Status code: " + str(user_response.status_code) + " Reason: " + user_response.text)

            user = user_response.json()
            return user["data"]["user"]
    except httpx.RequestError as exception:
        raise MqttClientCommunicationError("Could not read user data from the API. Reason: " + str(exception)) from exception
