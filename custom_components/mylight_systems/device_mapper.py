"""Device mapping for MyLight Systems integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    pass

from .const import LOGGER


class DeviceMapper:
    """Simplified device mapper with no mapping logic."""

    def __init__(self):
        """Initialize device mapper."""
        pass

    def get_sensor_entities(self, devices: List) -> List[Dict[str, Any]]:
        """Get all sensor entities from devices."""
        LOGGER.info("Device mapping disabled - no sensor entities returned")
        return []

    def get_switch_entities(self, devices: List) -> List[Dict[str, Any]]:
        """Get all switch entities from devices."""
        LOGGER.info("Device mapping disabled - no switch entities returned")
        return []
