"""Switch platform for mylight_systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from mylightsystems import MyLightSystemsError

from .const import DATA_COORDINATOR, DOMAIN, LOGGER
from .coordinator import MyLightSystemsDataUpdateCoordinator
from .device_mapper import DeviceMapper
from .entity import IntegrationMyLightSystemsEntity


@dataclass
class MyLightDeviceSwitchEntityDescription(SwitchEntityDescription):
    """Describes a device-based switch entity."""

    is_on_fn: Callable[[Any], bool] = lambda device: False
    turn_on_fn: Callable[[Any], Callable[[], Coroutine[Any, Any, None]] | None] = lambda device: None
    turn_off_fn: Callable[[Any], Callable[[], Coroutine[Any, Any, None]] | None] = lambda device: None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Configure switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    device_mapper = DeviceMapper()

    # Wait for initial data fetch
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data or not coordinator.data.devices:
        LOGGER.warning("No devices found from MyLight Systems API")
        return

    # Get switch entities from devices
    switch_entities = device_mapper.get_switch_entities(coordinator.data.devices)

    switches = []
    for entity_config in switch_entities:
        device = entity_config["device"]
        device_id = getattr(device, "id", None) or getattr(device, "device_id", None) or id(device)

        # Handle dynamic name (function or string)
        entity_name = entity_config["name"]
        if callable(entity_name):
            entity_name = entity_name(device)

        # Add device identifier in parentheses for clarity
        device_name = getattr(device, "name", str(device_id))
        full_name = f"{entity_name} ({device_name})" if entity_name != device_name else entity_name

        # Create entity description
        entity_description = MyLightDeviceSwitchEntityDescription(
            key=f"{device_id}_{entity_config['key']}",
            name=full_name,
            icon=entity_config.get("icon"),
            is_on_fn=entity_config["is_on_fn"],
            turn_on_fn=entity_config["turn_on_fn"],
            turn_off_fn=entity_config["turn_off_fn"],
        )

        switch = MyLightSystemsDeviceSwitch(
            entry_id=entry.entry_id,
            coordinator=coordinator,
            entity_description=entity_description,
            device=device,
        )
        switches.append(switch)

    if switches:
        async_add_entities(switches)
        LOGGER.info("Added %d device-based switches to unified MyLight Systems device", len(switches))
    else:
        LOGGER.info("No switch entities found in devices")


class MyLightSystemsDeviceSwitch(IntegrationMyLightSystemsEntity, SwitchEntity):
    """MyLight Systems Device-based Switch class."""

    def __init__(
        self,
        entry_id: str,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        entity_description: MyLightDeviceSwitchEntityDescription,
        device: Any,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_id = f"{DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self.entity_description = entity_description
        self._device = device

        # Set the name from the entity description
        self._attr_name = entity_description.name

        # Device info is inherited from the base class (unified device)
        # No need to override _attr_device_info as it's set in the parent class

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        try:
            current_device = self._find_current_device()
            if current_device is None:
                return False
            return self.entity_description.is_on_fn(current_device)
        except Exception as exc:
            LOGGER.error("Error getting switch state for %s: %s", self.entity_id, exc)
            return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._find_current_device() is not None

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            current_device = self._find_current_device()
            if current_device is None:
                LOGGER.error("Device not found for switch %s", self.entity_id)
                return

            turn_off_func = self.entity_description.turn_off_fn(current_device)
            if turn_off_func is None:
                LOGGER.error("No turn_off function available for switch %s", self.entity_id)
                return

            await turn_off_func()
            await self.coordinator.async_request_refresh()

        except MyLightSystemsError as exc:
            LOGGER.error("Error turning off switch %s: %s", self.entity_id, exc)
            self._attr_available = False
        except Exception as exc:
            LOGGER.error("Unexpected error turning off switch %s: %s", self.entity_id, exc)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            current_device = self._find_current_device()
            if current_device is None:
                LOGGER.error("Device not found for switch %s", self.entity_id)
                return

            turn_on_func = self.entity_description.turn_on_fn(current_device)
            if turn_on_func is None:
                LOGGER.error("No turn_on function available for switch %s", self.entity_id)
                return

            await turn_on_func()
            await self.coordinator.async_request_refresh()

        except MyLightSystemsError as exc:
            LOGGER.error("Error turning on switch %s: %s", self.entity_id, exc)
            self._attr_available = False
        except Exception as exc:
            LOGGER.error("Unexpected error turning on switch %s: %s", self.entity_id, exc)

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
