"""Constants for MyLight Systems library."""

DEFAULT_TIMEOUT_IN_SECONDS: int = 10

ERR_INVALID_CREDENTIALS: str = "invalid.credentials"
ERR_UNDEFINED_EMAIL: str = "undefined.email"
ERR_UNDEFINED_PASSWORD: str = "undefined.password"  # noqa: S105
ERR_NOT_AUTHORIZED: str = "not.authorized"
ERR_SWITCH_NOT_ALLOWED: str = "switch.not.allowed"

DEFAULT_BASE_URL: str = "https://myhome.mylight-systems.com"
AUTH_URL: str = "/api/auth"
PROFILE_URL: str = "/api/profile"
DEVICES_URL: str = "/api/devices"
MEASURES_TOTAL_URL: str = "/api/measures/total"
MEASURES_GROUPING_URL: str = "/api/measures/grouping"
STATES_URL: str = "/api/states"
SWITCH_URL: str = "/api/device/switch"
ROOMS_URL: str = "/api/rooms"
SCHEDULE_URL: str = "/api/schedule"
