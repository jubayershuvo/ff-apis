import requests


def get_ff_guest_jwt(uid, password, region):
    """
    Fetch FF guest JWT token

    Args:
        uid (str): User ID
        password (str): Password/hash
        region (str): Region code

    Returns:
        dict: JSON response from API
    """

    url = "http://127.0.0.1:5080/get_jwt"

    params = {
        "uid": uid,
        "password": password,
        "region": region
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": str(e)
        }


