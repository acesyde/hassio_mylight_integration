"""Constants for mylight_systems."""
from logging import getLogger
from logging import Logger

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import Platform
from homeassistant.const import UnitOfEnergy

LOGGER: Logger = getLogger(__package__)

# General
NAME = "MyLight Systems"
DOMAIN = "mylight_systems"
PLATFORMS = [Platform.SENSOR]
VERSION = "0.0.0"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.mylight-systems.com/"
SCAN_INTERVAL_IN_MINUTES = 15

# API
BASE_URL = "https://myhome.mylight-systems.com/api"
AUTH_PATH = "/auth"
PROFILE_PATH = "/profile"
DEVICES_PATH = "/devices"
MEASURES_TOTAL_PATH = "/measures/total"

# SENSORS
SENSORS = (
    SensorEntityDescription(
        key="production",
        name="Current Power Production",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="grid",
        name="Current power production returned to the grid",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
)
