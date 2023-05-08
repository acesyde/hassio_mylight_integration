"""Constants for mylight_systems."""
from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# General
NAME = "MyLight Systems"
DOMAIN = "mylight_systems"
PLATFORMS = [Platform.SENSOR]
VERSION = "0.0.5"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.mylight-systems.com/"
SCAN_INTERVAL_IN_MINUTES = 15

# Configuration
CONF_VIRTUAL_DEVICE_ID = "virtual_device_id"
CONF_VIRTUAL_BATTERY_ID = "virtual_battery_id"
CONF_MASTER_ID = "master_id"
CONF_MASTER_REPORT_PERIOD = "master_report_period"
CONF_SUBSCRIPTION_ID = "subscription_id"
CONF_GRID_TYPE = "grid_type"

# MyLight
# DEFAULT_BASE_URL: str = "https://myhome.mylight-systems.com"
