"""Sensor platform for mylight_systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, LOGGER
from .coordinator import (
    MyLightSystemsDataUpdateCoordinator,
)
from .device_mapper import DeviceMapper
from .entity import IntegrationMyLightSystemsEntity


@dataclass
class MyLightDeviceSensorEntityDescription(SensorEntityDescription):
    """Describes a device-based sensor entity."""

    value_fn: Callable[[Any], int | float | str | None] = lambda device: None
    attributes_fn: Callable[[Any], dict[str, Any]] | None = None
    device_info: dict[str, Any] | None = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback) -> None:
    """Configure sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    device_mapper = DeviceMapper()

    # Wait for initial data fetch
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data or not coordinator.data.devices:
        LOGGER.warning("No devices found from MyLight Systems API")
        return

    # Get sensor entities from devices
    sensor_entities = device_mapper.get_sensor_entities(coordinator.data.devices)

    sensors = []
    for entity_config in sensor_entities:
        device = entity_config["device"]
        device_id = getattr(device, "id", None) or getattr(device, "device_id", None) or id(device)

        # Handle dynamic name (function or string)
        entity_name = entity_config["name"]
        if callable(entity_name):
            entity_name = entity_name(device)

        # Add device identifier in parentheses for clarity
        full_name = (
            f"{entity_name} ({getattr(device, 'name', device_id)})"
            if entity_name != getattr(device, "name", device_id)
            else entity_name
        )

        # Create entity description
        entity_description = MyLightDeviceSensorEntityDescription(
            key=f"{device_id}_{entity_config['key']}",
            name=full_name,
            icon=entity_config.get("icon"),
            native_unit_of_measurement=entity_config.get("unit_of_measurement"),
            device_class=entity_config.get("device_class"),
            state_class=entity_config.get("state_class"),
            value_fn=entity_config["value_fn"],
            attributes_fn=entity_config.get("attributes_fn"),
            device_info=device_mapper.get_device_info(device),
        )

        sensor = MyLightSystemsDeviceSensor(
            entry_id=entry.entry_id,
            coordinator=coordinator,
            entity_description=entity_description,
            device=device,
        )
        sensors.append(sensor)

    if sensors:
        async_add_devices(sensors)
        LOGGER.info("Added %d device-based sensors", len(sensors))
    else:
        LOGGER.warning("No sensor entities could be created from devices")


class MyLightSystemsDeviceSensor(IntegrationMyLightSystemsEntity, SensorEntity):
    """MyLight Systems Device-based Sensor class."""

    def __init__(
        self,
        entry_id: str,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        entity_description: MyLightDeviceSensorEntityDescription,
        device: Any,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_id = f"{DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self.entity_description = entity_description
        self._device = device

        # Set device info for device registry
        if entity_description.device_info:
            self._attr_device_info = entity_description.device_info

    @property
    def native_value(self) -> int | float | str | None:
        """Return the state of the sensor."""
        try:
            # Find the current device in coordinator data
            current_device = self._find_current_device()
            if current_device is None:
                LOGGER.warning("Device not found in coordinator data for sensor %s", self.entity_id)
                return None

            return self.entity_description.value_fn(current_device)
        except Exception as exc:
            LOGGER.error("Error getting sensor value for %s: %s", self.entity_id, exc)
            return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._find_current_device() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if not self.entity_description.attributes_fn:
            return None

        try:
            current_device = self._find_current_device()
            if current_device is None:
                return None

            return self.entity_description.attributes_fn(current_device)
        except Exception as exc:
            LOGGER.error("Error getting sensor attributes for %s: %s", self.entity_id, exc)
            return None

    def _find_current_device(self) -> Any | None:
        """Find the current device in coordinator data."""
        if not self.coordinator.data or not self.coordinator.data.devices:
            return None

        device_id = getattr(self._device, "id", None) or getattr(self._device, "device_id", None)
        if device_id is None:
            # Fallback to object comparison if no ID available
            return self._device if self._device in self.coordinator.data.devices else None

        # Find device by ID
        for device in self.coordinator.data.devices:
            current_device_id = getattr(device, "id", None) or getattr(device, "device_id", None)
            if current_device_id == device_id:
                return device

        return None
