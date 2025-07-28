"""Base entity classes for MyLight Systems integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, LOGGER, NAME
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
        self._attr_unique_id = f"{DOMAIN}_{device_id}"

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
            sw_version=getattr(self._device, "sw_version", None),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self._device is not None and getattr(self._device, "state", True)
        )


class MyLightSystemsSensorEntity(MyLightSystemsEntity):
    """Base sensor entity for MyLight Systems devices."""

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        device_id: str,
        sensor_id: str,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator, device_id)
        self._sensor_id = sensor_id
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}"

        # Find the device state and sensor state
        self._device_state = None
        self._sensor_state = None

        for state in coordinator.data.states:
            if state.device_id == device_id:
                self._device_state = state
                # Find the specific sensor state
                for sensor_state in state.sensor_states:
                    if sensor_state.sensor_id == sensor_id:
                        self._sensor_state = sensor_state
                        break
                break

        if not self._sensor_state:
            LOGGER.error("Sensor %s not found for device %s", sensor_id, device_id)

    def _get_current_sensor_state(self):
        """Get the current sensor state from coordinator data."""
        if not self.coordinator.data or not self.coordinator.data.states:
            return None

        for state in self.coordinator.data.states:
            if state.device_id == self._device_id:
                for sensor_state in state.sensor_states:
                    if sensor_state.sensor_id == self._sensor_id:
                        return sensor_state
        return None

    @property
    def available(self) -> bool:
        """Return True if sensor is available."""
        return super().available and self._get_current_sensor_state() is not None
