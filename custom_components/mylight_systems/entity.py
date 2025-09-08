"""Base entity classes for MyLight Systems integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_SUBSCRIPTION_ID, DOMAIN, LOGGER, NAME
from .coordinator import MyLightSystemsDataUpdateCoordinator


class MyLightSystemsEntity(CoordinatorEntity[MyLightSystemsDataUpdateCoordinator]):
    """Base entity for MyLight Systems devices."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id

        # Get subscription_id from config entry and convert to lowercase
        subscription_id = coordinator.config_entry.data[CONF_SUBSCRIPTION_ID]
        self._attr_unique_id = f"{str(subscription_id)}_{device_id.replace('-', '_')}".lower()

        # Find the device in coordinator data
        self._device = None
        for device in coordinator.data.devices:
            if device.id == device_id:
                self._device = device
                break

        if not self._device:
            LOGGER.error("Device %s not found in coordinator data", device_id)
            return

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._device.name,
            manufacturer=NAME,
            model=self._device.device_type_name,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self._device is not None and getattr(self._device, "state", True)
        )
