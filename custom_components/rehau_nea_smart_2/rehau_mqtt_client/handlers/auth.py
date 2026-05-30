"""Auth handler for Rehau NEA Smart 2.

REHAU's account server (``accounts.rehau.com``, a Cidaas OAuth2 install) now
enforces e-mail based multi-factor authentication (MFA) on login. The previous
single-POST login flow therefore stopped working: the login no longer returns
an authorization ``code`` directly, it returns an MFA challenge instead.

This module implements the full interactive flow without a headless browser:

1. ``RehauAuthSession.start(email, password)`` performs the OAuth authorize
   request and the username/password login. It returns ``"complete"`` (no MFA
   required) or ``"mfa"`` (a verification code has to be entered).
2. ``RehauAuthSession.request_email_code()`` asks REHAU to e-mail a 6-digit
   verification code to the account.
3. ``RehauAuthSession.submit_code(code)`` verifies the code, finishes the OAuth
   flow and exchanges the authorization code for tokens.

After the one-time interactive login the integration only ever uses the
``refresh`` token, so MFA is not needed again on Home Assistant restarts.
"""
import logging
import secrets
from urllib.parse import urlparse, parse_qs, urljoin, quote

import httpx

from ..exceptions import (
    MqttClientAuthenticationError,
    MqttClientCommunicationError,
)
from ..utils.hashing import convert_challenge

_LOGGER = logging.getLogger(__name__)

CLIENT_ID = "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1"
CLIENT_SECRET = "10edca85-0623-48ad-bbbe-76b5e4ec89a9"
AUTH_URL_ROLES = "email roles profile offline_access"
# Must match a redirect URI registered for the client. Kept identical to the
# value that worked before MFA was introduced. We never actually fetch it - the
# authorization code is read straight out of the redirect ``Location`` header.
# Canonical (decoded) form, used for the token exchange and code detection.
AUTH_URL_REDIRECT = "http://localhost:3000/#!/auth-code"
# Partially-encoded form (only the '#' escaped) used verbatim in the authorize
# query string, exactly as the previously-working version sent it.
AUTH_URL_REDIRECT_AUTHZ = "http://localhost:3000/%23!/auth-code"
AUTH_URL_ORIGIN = "https://accounts.rehau.com"

# A browser-like User-Agent. Cidaas rejects some non-browser agents.
_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; sdk_gphone_x86 Build/RSR1.201013.001; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 "
    "Mobile Safari/537.36"
)

_MAX_REDIRECTS = 10


def _first(value):
    """Return the first element of a parse_qs value list, or None."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


async def fetch_user_data(email: str, access_token: str) -> dict:
    """Fetch the user object (installations, default install, ...) for an account.

    Args:
        email: The account e-mail.
        access_token: A valid OAuth access token.

    Returns:
        dict: The ``user`` object as returned by the REHAU cloud API.

    Raises:
        MqttClientAuthenticationError: If the API rejects the token.
        MqttClientCommunicationError: On any other API error.
    """
    url = f"https://api.nea2aws.aws.rehau.cloud/v1/users/{email}/getUserData"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            url, headers={"Authorization": "Bearer " + access_token}
        )
    if response.status_code == 401:
        raise MqttClientAuthenticationError(
            "Could not get user data (401). Token rejected."
        )
    if response.status_code != 200:
        raise MqttClientCommunicationError(
            "Could not get user data. Status code: "
            + str(response.status_code)
            + " Reason: "
            + response.text
        )
    return response.json()["data"]["user"]


class RehauAuthSession:
    """Stateful holder for the multi-step REHAU OAuth/MFA login.

    Cookies set during the OAuth authorize and login steps are required by the
    later MFA calls, so they are kept in a shared jar on the session. A fresh
    ``httpx.AsyncClient`` is created per request (reusing the jar) so no
    connection is held open while the user types the verification code.
    """

    def __init__(self):
        # PKCE verifier (43-128 chars). The challenge is its SHA-256, base64url.
        self.code_verifier = secrets.token_urlsafe(48)
        self.cookies = httpx.Cookies()
        self.email: str | None = None
        self.track_id: str | None = None
        self.sub: str | None = None
        self.request_id: str | None = None
        self.medium_id: str | None = None
        self.exchange_id: str | None = None
        self._auth_code: str | None = None

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            cookies=self.cookies,
            follow_redirects=False,
            timeout=30,
            headers={"User-Agent": _USER_AGENT},
        )

    async def _build_authz_url(self) -> str:
        code_challenge = await convert_challenge(self.code_verifier)
        nonce = secrets.token_urlsafe(32)
        # Build manually to control encoding exactly as REHAU expects.
        params = (
            f"client_id={CLIENT_ID}"
            f"&scope={quote(AUTH_URL_ROLES)}"
            f"&response_type=code"
            f"&redirect_uri={AUTH_URL_REDIRECT_AUTHZ}"
            f"&nonce={nonce}"
            f"&code_challenge_method=S256"
            f"&code_challenge={code_challenge}"
        )
        return f"{AUTH_URL_ORIGIN}/authz-srv/authz?{params}"

    @staticmethod
    def _params_from_url(url: str) -> dict:
        """Parse query params from a URL, checking both the query and #fragment."""
        if not url:
            return {}
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if parsed.fragment and "=" in parsed.fragment:
            # Angular-style "#!/page?a=b" or "#a=b" fragments.
            frag = parsed.fragment
            if "?" in frag:
                frag = frag.split("?", 1)[1]
            params.update(parse_qs(frag))
        return params

    @staticmethod
    def _extract_code(location: str) -> str | None:
        """Pull the OAuth ``code`` out of a redirect Location (handles #fragment)."""
        if not location:
            return None
        # The redirect URI uses a #! fragment; query may sit in either part.
        candidates = [location]
        if "#" in location:
            candidates.append(location.split("#", 1)[1])
        for candidate in candidates:
            parsed = urlparse(candidate)
            query = parse_qs(parsed.query)
            if "code" in query:
                return _first(query["code"])
            # Some redirects place the code after the fragment marker.
            if "code=" in candidate:
                frag = candidate.split("code=", 1)[1]
                return frag.split("&")[0]
        return None

    async def _walk_redirects(self, client, response):
        """Follow same-origin redirects until an auth code or a non-redirect.

        Never fetches the (localhost) redirect URI - if a Location carries the
        code, it is returned immediately.

        Returns:
            tuple(code, last_url): ``code`` is the authorization code if found,
            else None. ``last_url`` is the absolute URL we last navigated to
            (e.g. the MFA page, so its query params can be inspected).
        """
        redirect_base = AUTH_URL_REDIRECT.split("#", 1)[0]
        location = response.headers.get("Location")
        last_url = str(response.url)
        hops = 0
        while response.status_code in (301, 302, 303, 307, 308) and location:
            code = self._extract_code(location)
            if code:
                return code, location
            if location.startswith(redirect_base):
                # Reached the (localhost) redirect URI without a code.
                return None, location
            hops += 1
            if hops > _MAX_REDIRECTS:
                _LOGGER.error("Too many redirects while following auth flow")
                return None, last_url
            next_url = urljoin(str(response.url), location)
            response = await client.get(next_url)
            last_url = next_url
            location = response.headers.get("Location")
        return None, last_url

    async def _exchange_token(self, client) -> dict:
        """Exchange the stored authorization code for tokens."""
        token_response = await client.post(
            AUTH_URL_ORIGIN + "/token-srv/token",
            data={
                "client_id": CLIENT_ID,
                "code": self._auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": AUTH_URL_REDIRECT,
                "code_verifier": self.code_verifier,
            },
        )
        if token_response.status_code != 200:
            _LOGGER.error(
                "Token exchange failed: %s %s",
                token_response.status_code,
                token_response.text,
            )
            raise MqttClientAuthenticationError(
                "Could not exchange authorization code for token "
                f"(status {token_response.status_code})"
            )
        return token_response.json()

    async def start(self, email: str, password: str):
        """Perform the authorize + login step.

        Returns:
            One of:
              - ("complete", token_data, user) when no MFA is required.
              - ("mfa", None, None) when an e-mail verification code is needed.

        Raises:
            MqttClientAuthenticationError: On invalid credentials.
            MqttClientCommunicationError: On unexpected server responses.
        """
        self.email = email
        async with self._client() as client:
            authz_url = await self._build_authz_url()
            _LOGGER.debug("Requesting authorize endpoint")
            authz_resp = await client.get(authz_url)
            location = authz_resp.headers.get("Location")
            if not location:
                raise MqttClientCommunicationError(
                    "No redirect from authorize endpoint (status "
                    f"{authz_resp.status_code})"
                )
            query = parse_qs(urlparse(location).query)
            if "requestId" not in query:
                # Follow one more hop in case authorize bounced through a page.
                location_resp = await client.get(urljoin(authz_url, location))
                location = location_resp.headers.get("Location", location)
                query = parse_qs(urlparse(location).query)
            if "requestId" not in query:
                raise MqttClientCommunicationError("No requestId found in login flow")
            self.request_id = _first(query["requestId"])

            _LOGGER.debug("Submitting credentials")
            login_resp = await client.post(
                AUTH_URL_ORIGIN + "/login-srv/login",
                data={
                    "username": email,
                    "username_type": "email",
                    "password": password,
                    "requestId": self.request_id,
                    "rememberMe": "true",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": AUTH_URL_ORIGIN,
                    "Referer": AUTH_URL_ORIGIN
                    + f"/rehau-ui/login?requestId={self.request_id}&view_type=login",
                },
            )

            if login_resp.status_code != 302:
                _LOGGER.error(
                    "Login did not redirect (status %s): %s",
                    login_resp.status_code,
                    login_resp.text[:500],
                )
                raise MqttClientAuthenticationError(
                    "Login failed - check e-mail and password"
                )

            location = login_resp.headers.get("Location", "")
            _LOGGER.debug("Login redirect received")

            # Case 1: authorization code straight away (no MFA configured).
            code, last = await self._walk_redirects(client, login_resp)
            if code:
                self._auth_code = code
                token_data = await self._exchange_token(client)
                user = await fetch_user_data(email, token_data["access_token"])
                return "complete", token_data, user

            # Case 2: MFA challenge. The mfa page URL carries the context.
            mfa_query = self._params_from_url(last or location)
            self.track_id = _first(mfa_query.get("track_id"))
            self.sub = _first(mfa_query.get("sub"))
            if mfa_query.get("requestId"):
                self.request_id = _first(mfa_query["requestId"])

            if not self.track_id or not self.sub:
                _LOGGER.error(
                    "Unexpected login redirect, no code and no MFA context: %s",
                    last or location,
                )
                raise MqttClientCommunicationError(
                    "Unexpected login response - no code and no MFA challenge"
                )
            _LOGGER.debug("MFA challenge detected")
            return "mfa", None, None

    async def request_email_code(self) -> None:
        """Ask REHAU to send the e-mail verification code.

        Looks up the configured e-mail MFA medium and initiates verification.

        Raises:
            MqttClientCommunicationError: If the MFA setup cannot be read.
        """
        mfa_referer = (
            f"{AUTH_URL_ORIGIN}/rehau-ui/mfa?track_id={self.track_id}"
            f"&sub={self.sub}&q={self.sub}&requestId={self.request_id}"
        )
        async with self._client() as client:
            # Establish session context by visiting the MFA page.
            await client.get(
                mfa_referer,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,*/*;q=0.8",
                    "Referer": AUTH_URL_ORIGIN + "/login-srv/login",
                },
            )

            configured = await client.post(
                AUTH_URL_ORIGIN
                + "/verification-srv/v2/setup/public/configured/list",
                json={"request_id": self.request_id, "sub": self.sub},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": AUTH_URL_ORIGIN,
                    "Referer": mfa_referer,
                },
            )
            if configured.status_code >= 400:
                _LOGGER.error(
                    "Configured MFA methods request failed: %s %s",
                    configured.status_code,
                    configured.text,
                )
                raise MqttClientCommunicationError(
                    "Could not read configured MFA methods"
                )
            self.medium_id = self._extract_medium_id(configured.json())
            _LOGGER.debug("Resolved MFA medium id")

            initiate = await client.post(
                AUTH_URL_ORIGIN
                + "/verification-srv/v2/authenticate/initiate/email",
                json={
                    "sub": self.sub,
                    "medium_id": self.medium_id,
                    "request_id": self.request_id,
                    "usage_type": "MULTIFACTOR_AUTHENTICATION",
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": AUTH_URL_ORIGIN,
                    "Referer": mfa_referer,
                },
            )
            if initiate.status_code >= 400:
                _LOGGER.error(
                    "Initiate e-mail MFA failed: %s %s",
                    initiate.status_code,
                    initiate.text,
                )
                raise MqttClientCommunicationError(
                    "Could not initiate e-mail verification"
                )
            self.exchange_id = self._extract_exchange_id(initiate.json())
            _LOGGER.info("Verification e-mail requested from REHAU")

            # Visit the verify page to keep the session aligned (best-effort).
            try:
                await client.get(
                    f"{AUTH_URL_ORIGIN}/rehau-ui/mfaverify/{self.exchange_id}"
                    f"/email/{self.sub}/{self.medium_id}/{self.request_id}",
                    headers={"Referer": mfa_referer},
                )
            except httpx.HTTPError as err:  # non-critical
                _LOGGER.debug("MFA verify page visit failed (ignored): %s", err)

    async def submit_code(self, code: str):
        """Verify the e-mail code and finish the OAuth flow.

        Args:
            code: The 6-digit verification code from the e-mail.

        Returns:
            tuple(token_data, user)

        Raises:
            MqttClientAuthenticationError: If the code is wrong/expired.
            MqttClientCommunicationError: On unexpected server responses.
        """
        mfa_verify_referer = (
            f"{AUTH_URL_ORIGIN}/rehau-ui/mfaverify/{self.exchange_id}"
            f"/email/{self.sub}/{self.medium_id}/{self.request_id}"
        )
        async with self._client() as client:
            verify = await client.post(
                AUTH_URL_ORIGIN
                + "/verification-srv/v2/authenticate/authenticate/email",
                json={
                    "pass_code": code,
                    "exchange_id": self.exchange_id,
                    "sub": self.sub,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                    "Origin": AUTH_URL_ORIGIN,
                    "Referer": mfa_verify_referer,
                },
            )
            if verify.status_code >= 400:
                _LOGGER.error(
                    "MFA code verification failed: %s %s",
                    verify.status_code,
                    verify.text,
                )
                raise MqttClientAuthenticationError(
                    "Verification code rejected - check the code and retry"
                )
            verify_data = verify.json()
            status_id = verify_data.get("data", {}).get("status_id") or verify_data.get(
                "status_id"
            )
            if not status_id:
                _LOGGER.error("No status_id in verify response: %s", verify_data)
                raise MqttClientCommunicationError(
                    "Verification succeeded but no status_id returned"
                )

            continue_resp = await client.post(
                AUTH_URL_ORIGIN + f"/login-srv/precheck/continue/{self.track_id}",
                data={
                    "status_id": status_id,
                    "track_id": self.track_id,
                    "requestId": self.request_id,
                    "sub": self.sub,
                    "verificationType": "EMAIL",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            code_value, last = await self._walk_redirects(client, continue_resp)
            if not code_value:
                _LOGGER.error(
                    "No authorization code after MFA continue. Last location: %s",
                    last,
                )
                raise MqttClientCommunicationError(
                    "MFA completed but no authorization code was returned"
                )

            self._auth_code = code_value
            token_data = await self._exchange_token(client)
            user = await fetch_user_data(self.email, token_data["access_token"])
            return token_data, user

    @staticmethod
    def _extract_medium_id(payload: dict) -> str:
        """Extract the e-mail MFA medium id from a configured/list response."""
        data = payload.get("data", payload)
        configured_list = data.get("configured_list")
        if isinstance(configured_list, list):
            for item in configured_list:
                if item.get("type") == "EMAIL":
                    mediums = item.get("mediums") or []
                    if mediums:
                        return mediums[0].get("medium_id") or mediums[0].get("id")
        raise MqttClientCommunicationError(
            "No e-mail MFA method configured on the REHAU account"
        )

    @staticmethod
    def _extract_exchange_id(payload: dict) -> str:
        """Extract the exchange id from an initiate/email response."""
        data = payload.get("data", {})
        exchange = data.get("exchange_id")
        if isinstance(exchange, str):
            return exchange
        if isinstance(exchange, dict) and exchange.get("exchange_id"):
            return exchange["exchange_id"]
        if data.get("status_id"):
            return data["status_id"]
        raise MqttClientCommunicationError(
            "No exchange_id returned when initiating e-mail verification"
        )


async def refresh(refresh_token):
    """Handle the refresh of the authentication token.

    Args:
        refresh_token: The stored refresh token.

    Returns:
        dict: The new token data.

    Raises:
        MqttClientAuthenticationError: If the refresh token is no longer valid.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            AUTH_URL_ORIGIN + "/token-srv/token",
            data={
                "client_id": CLIENT_ID,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "client_secret": CLIENT_SECRET,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        if token_response.status_code >= 400:
            raise MqttClientAuthenticationError(
                "Could not refresh token (status code {}) (response: {})".format(
                    token_response.status_code, token_response.text
                )
            )

        return token_response.json()
