"""MyLight Systems base entity."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import MyLightSystemsDataUpdateCoordinator


class IntegrationMyLightSystemsEntity(CoordinatorEntity[MyLightSystemsDataUpdateCoordinator]):
    """Base class for MyLight Systems entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: MyLightSystemsDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )
