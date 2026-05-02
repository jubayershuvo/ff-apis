import requests


def get_ff_guest_jwt(uid, password):
    """
    Fetch FF guest JWT token

    Args:
        uid (str): User ID
        password (str): Password/hash

    Returns:
        dict: JSON response from API
    """

    url = "https://get-ff-guest-jwt.vercel.app/get_jwt"

    params = {
        "uid": uid,
        "password": password
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


