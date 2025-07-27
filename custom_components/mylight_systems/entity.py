"""MyLightSystemsEntity Integration class."""

from __future__ import annotations

from homeassistant.const import CONF_EMAIL
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import MyLightSystemsDataUpdateCoordinator


class IntegrationMyLightSystemsEntity(CoordinatorEntity):
    """MyLightSystemsEntity Integration class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: MyLightSystemsDataUpdateCoordinator) -> None:
        """Initialize MyLightSystemsEntity Integration."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id

        # Create a unified device for the entire integration
        user_email = coordinator.config_entry.data.get(CONF_EMAIL, "unknown")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=user_email,
            model="MyLight Integration",
            manufacturer=NAME,
            sw_version=VERSION,
            configuration_url="https://www.mylight-systems.com/",
        )
