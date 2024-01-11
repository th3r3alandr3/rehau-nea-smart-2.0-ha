import secrets
import requests as request
from urllib.parse import urlparse, parse_qs
from ..utils.helpers import generate_auth_url
from homeassistant.core import HomeAssistant

async def auth(hass: HomeAssistant, email, password, check_credentials = False):
    challenge = secrets.token_urlsafe(16)
    url = await generate_auth_url(
        "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1",
        "email%20roles%20profile%20offline_access",
        "http://localhost:3000/%23!/auth-code",
        "https://accounts.rehau.com",
        challenge
    )
    login_site = await hass.async_add_executor_job(request.get, url)
    parsed_url = urlparse(login_site.url)
    query = parse_qs(parsed_url.query)
    if "requestId" not in query:
        raise Exception("No request id found")
    request_id = query["requestId"][0]
    data = {
        "username": email,
        "username_type": "email",
        "password": password,
        "requestId": request_id,
        "rememberMe": "true",
    }

    response = await hass.async_add_executor_job(lambda: request.post("https://accounts.rehau.com/login-srv/login", data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://accounts.rehau.com",
        "Referer": "https://accounts.rehau.com/rehau-ui/login?requestId={}&view_type=login".format(request_id),
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; sdk_gphone_x86 Build/RSR1.201013.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36",
    }, allow_redirects=False))

    if not response.is_redirect:
        if check_credentials:
            return False
        raise Exception("No redirect found")

    redirect_url = response.headers["Location"]
    parsed_url = urlparse(redirect_url)
    queries = parse_qs(parsed_url.query)
    for key in queries:
        queries[key] = queries[key][0]

    if "code" not in queries:
        if check_credentials:
            return False
        raise Exception("No code found")

    token_response = await hass.async_add_executor_job(lambda: request.post("https://accounts.rehau.com/token-srv/token", data={
        "client_id": "3f5d915d-a06f-42b9-89cc-2e5d63aa96f1",
        "code": queries["code"],
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:3000/#!/auth-code",
        "code_verifier": challenge,
    }, allow_redirects=False))

    if token_response.status_code != 200:
        if check_credentials:
            return False
        raise Exception("Could not get token")

    if check_credentials:
        return True

    token_data = token_response.json()
    return token_data
