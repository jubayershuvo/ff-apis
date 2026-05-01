import os
import json
import random
from datetime import datetime, timezone

from lib.get_guest_jwt import get_ff_guest_jwt


ACCOUNTS_FILE = "accounts.json"
JWT_FILE = "jwt.json"


# -----------------------------
# Utils
# -----------------------------

def load_json(path):
    if not os.path.exists(path):
        return {} if "accounts" in path else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {} if "accounts" in path else []


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_expired(timestamp):
    if not timestamp:
        return True
    now = int(datetime.now(timezone.utc).timestamp())
    return now >= int(timestamp)


# -----------------------------
# Core JWT Manager
# -----------------------------

class JWTManager:
    def __init__(self):
        self.accounts = load_json(ACCOUNTS_FILE)
        self.jwt_store = load_json(JWT_FILE)

    # -------------------------
    # Get cached JWT
    # -------------------------
    def get_cached(self, uid):
        return next((x for x in self.jwt_store if str(x.get("uid")) == str(uid)), None)

    # -------------------------
    # Save / update JWT
    # -------------------------
    def save_jwt(self, entry):
        self.jwt_store = [
            x for x in self.jwt_store if str(x.get("uid")) != str(entry["uid"])
        ]
        self.jwt_store.append(entry)
        save_json(JWT_FILE, self.jwt_store)

    # -------------------------
    # Fetch new JWT
    # -------------------------
    def fetch_jwt(self, uid, password, region):
        res = get_ff_guest_jwt(uid=uid, password=password)

        if not res.get("jwt_token"):
            return None

        return {
            "uid": uid,
            "password": password,
            "region": region,
            "jwt_token": res["jwt_token"],
            "access_token": res.get("access_token"),
            "expiry": res.get("expiry", {})
        }

    # -------------------------
    # Main function
    # -------------------------
    def get_jwt_if_not(self, region):
        """
        Fast JWT retrieval system:
        - random account selection
        - cache-first
        - refresh only when needed
        """

        accounts = self.accounts.get(region, [])

        if not accounts:
            return {
                "success": False,
                "message": f"No accounts found for region {region}"
            }

        random.shuffle(accounts)

        for acc in accounts:
            uid = str(acc["uid"])
            password = acc["password"]
            region = acc.get("region", region)

            # 1️⃣ Check cache first
            cached = self.get_cached(uid)

            if cached:
                exp = cached.get("expiry", {}).get("timestamp")

                if cached.get("jwt_token") and not is_expired(exp):
                    return {
                        "success": True,
                        "source": "cache",
                        "uid": uid,
                        "jwt_token": cached["jwt_token"],
                        "access_token": cached.get("access_token"),
                        "expiry": cached.get("expiry")
                    }

            # 2️⃣ Fetch new JWT if expired/missing
            print(f"[JWT] Refreshing UID: {uid} ({region})")

            new_data = self.fetch_jwt(uid, password, region)

            if not new_data:
                continue

            self.save_jwt(new_data)

            return {
                "success": True,
                "source": "fresh",
                "uid": uid,
                "jwt_token": new_data["jwt_token"],
                "access_token": new_data["access_token"],
                "expiry": new_data["expiry"]
            }

        return {
            "success": False,
            "message": "No valid JWT available"
        }


# -----------------------------
# Simple usage function wrapper
# -----------------------------

def get_jwt_if_not(region):
    manager = JWTManager()
    return manager.get_jwt_if_not(region)