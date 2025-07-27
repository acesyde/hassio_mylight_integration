"""Constants for mylight_systems."""

from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# General
NAME = "MyLight Systems"
DOMAIN = "mylight_systems"
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]
VERSION = "1.0.0"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.mylight-systems.com/"
SCAN_INTERVAL_IN_MINUTES = timedelta(minutes=15)

# Configuration
CONF_SUBSCRIPTION_ID = "subscription_id"
CONF_GRID_TYPE = "grid_type"

# Data
DATA_COORDINATOR = "coordinator"
