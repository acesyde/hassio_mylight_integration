"""Constants for MyLight Systems library."""
from __future__ import annotations

DEFAULT_TIMEOUT_IN_SECONDS: int = 10

BASE_URL: str = "https://myhome.mylight-systems.com"
AUTH_URL: str = f"{BASE_URL}/api/auth"
PROFILE_URL: str = f"{BASE_URL}/api/profile"
DEVICES_URL: str = f"{BASE_URL}/api/devices"
STATES_URL: str = f"{BASE_URL}/states"
MEASURES_TOTAL_URL: str = f"{BASE_URL}/measures/total"
