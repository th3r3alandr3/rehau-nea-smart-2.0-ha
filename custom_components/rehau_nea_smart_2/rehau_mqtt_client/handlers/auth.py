"""Auth handler for Rehau NEA Smart 2."""
import logging
import secrets
import httpx
from urllib.parse import urlparse, parse_qs

from ..exceptions import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
)
from ..utils import generate_auth_url
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def auth(email, password, check_credentials=False):
    """Authenticate with Rehau NEA Smart 2."""

    challenge = secrets.token_urlsafe(16)
    url = await generate_auth_url(
        "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1",
        "email%20roles%20profile%20offline_access",
        "http://localhost:3000/%23!/auth-code",
        "https://accounts.rehau.com",
        challenge
    )
    async with httpx.AsyncClient() as client:
        _LOGGER.debug("Getting login site")
        login_site = await client.get(url, timeout=30)
        parsed_url = urlparse(login_site.headers["Location"])
        query = parse_qs(parsed_url.query)
        if "requestId" not in query:
            raise MqttClientCommunicationError("No request id found")
        request_id = query["requestId"][0]
        data = {
            "username": email,
            "username_type": "email",
            "password": password,
            "requestId": request_id,
            "rememberMe": "true",
        }

        response = await client.post("https://accounts.rehau.com/login-srv/login", timeout=30, data=data, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://accounts.rehau.com",
            "Referer": "https://accounts.rehau.com/rehau-ui/login?requestId={}&view_type=login".format(request_id),
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; sdk_gphone_x86 Build/RSR1.201013.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36",
        })

        if response.status_code != 302:
            _LOGGER.error("No redirect found")
            if check_credentials:
                return False
            raise MqttClientAuthenticationError("No redirect found")

        redirect_url = response.headers["Location"]
        parsed_url = urlparse(redirect_url)
        queries = parse_qs(parsed_url.query)
        for key in queries:
            queries[key] = queries[key][0]

        if "code" not in queries:
            _LOGGER.error("No code found")
            if check_credentials:
                return False
            raise MqttClientAuthenticationError("No code found")

        token_response = await client.post("https://accounts.rehau.com/token-srv/token", timeout=30, data={
            "client_id": "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1",
            "code": queries["code"],
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:3000/#!/auth-code",
            "code_verifier": challenge,
        })

        if token_response.status_code != 200:
            _LOGGER.error("Could not get token")
            if check_credentials:
                return False
            raise MqttClientAuthenticationError("Could not get token")

        _LOGGER.debug("Got token")
        if check_credentials:
            return True

        token_data = token_response.json()

        user_response = await client.get(f"https://api.nea2aws.aws.rehau.cloud/v1/users/{email}/getUserData", timeout=30,
                                headers={"Authorization": "Bearer " + token_data["access_token"]})

        if user_response.status_code != 200:
            raise MqttClientAuthenticationError("Could not get user data")

        user = user_response.json()

        return token_data, user["data"]["user"]

async def refresh(refresh_token):
    """Handle the refresh of the authentication token."""

    async with httpx.AsyncClient() as client:
        token_response = await client.post("https://accounts.rehau.com/token-srv/token", timeout=30, data={
            "client_id": "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_secret": "10edca85-0623-48ad-bbbe-76b5e4ec89a9",
        }, headers={
            "Content-Type": "application/json",
        })

        if token_response.status_code >= 400:
            _LOGGER.error("Could not refresh token")
            raise MqttClientAuthenticationError("Could not refresh token (status code {}) (response: {})".format(token_response.status_code, token_response.text))

        token_data = token_response.json()

        return token_data

