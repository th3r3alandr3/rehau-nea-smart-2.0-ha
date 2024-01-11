import requests


def handle_refresh(refresh_token):
    try:
        headers = {"Content-type": "application/json"}
        data = {"token": refresh_token}
        refresh_url = f"https://api.neasmart2.app.rehau.com/v2/api/authentication/refresh"
        refreshInProcess = requests.post(refresh_url, json=data, headers=headers)

        response = refreshInProcess.json()

        return response

    except Exception as e:
        print(e)
        return None
