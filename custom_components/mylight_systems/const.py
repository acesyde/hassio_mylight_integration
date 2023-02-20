"""Constants for mylight_systems."""
from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# General
NAME = "MyLight Systems"
DOMAIN = "mylight_systems"
PLATFORMS = [Platform.SENSOR]
VERSION = "0.0.0"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.mylight-systems.com/"
SCAN_INTERVAL_IN_MINUTES = 15

# Configuration
CONF_VIRTUAL_DEVICE_ID = "virtual_device_id"
CONF_VIRTUAL_BATTERY_ID = "virtual_battery_id"

# API
BASE_URL = "https://myhome.mylight-systems.com/api"
AUTH_PATH = "/auth"
PROFILE_PATH = "/profile"
DEVICES_PATH = "/devices"
MEASURES_TOTAL_PATH = "/measures/total"
