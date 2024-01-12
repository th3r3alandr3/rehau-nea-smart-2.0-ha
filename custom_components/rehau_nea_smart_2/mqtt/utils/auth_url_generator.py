"""Generate the authentication URL based on the provided parameters."""
import secrets
from .hashing import convert_challenge

async def generate_auth_url(client_id, scopes, redirect_uri, url, challenge):
    """Generate the authentication URL based on the provided parameters.

    Args:
        client_id (str): The client ID.
        scopes (str): The scopes.
        redirect_uri (str): The redirect URI.
        url (str): The base URL.
        challenge (str): The challenge string.

    Returns:
        str: The generated authentication URL.
    """
    nonce = secrets.token_urlsafe(32)

    converted_challenge = await convert_challenge(challenge)
    e = (
        f"client_id={client_id}&"
        f"scope={scopes}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"nonce={nonce}&"
        f"code_challenge_method=S256&"
        f"code_challenge={converted_challenge}"
    )

    return f"{url}/authz-srv/authz?{e}"
