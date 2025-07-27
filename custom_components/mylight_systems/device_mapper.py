"""Device mapping for MyLight Systems integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    pass

from .const import LOGGER

# Device type to entity mapping
DEVICE_TYPE_MAPPINGS = {
    "mst": {
        "platform": "sensor",
        "entities": [
            {
                "key": "master_device",
                "name": lambda device: getattr(device, "name", "Master Device"),
                "icon": "mdi:power-plug",
                "value_fn": lambda device, states: _get_state_value(
                    device, states, "state", fallback=getattr(device, "state", False)
                ),
                "attributes_fn": lambda device: {
                    "device_type_name": getattr(device, "device_type_name", None),
                    "report_period": getattr(device, "report_period", None),
                    "type_id": getattr(device, "type_id", None),
                    "device_id": getattr(device, "id", None),
                },
            }
        ],
    },
    "bat": {
        "platform": "sensor",
        "entities": [
            {
                "key": "battery_capacity",
                "name": lambda device: f"{getattr(device, 'name', 'My Smart Battery')} Capacity",
                "icon": "mdi:battery-charging",
                "device_class": "power",
                "state_class": "measurement",
                "unit_of_measurement": "kW",
                # Manual value specification: Use states from API or fallback to device attribute
                "value_fn": lambda device, states: _get_battery_capacity_value(device, states),
                "attributes_fn": lambda device: {
                    "device_type_name": getattr(device, "device_type_name", None),
                    "type_id": getattr(device, "type_id", None),
                    "device_id": getattr(device, "id", None),
                },
            },
        ],
    },
    "vrt": {
        "platform": "sensor",
        "entities": [
            {
                "key": "virtual_device",
                "name": lambda device: getattr(device, "name", "Virtual Device"),
                "icon": "mdi:cloud-outline",
                "value_fn": lambda device, states: _get_virtual_device_value(device, states),
                "attributes_fn": lambda device: {
                    "device_type_name": getattr(device, "device_type_name", None),
                    "type_id": getattr(device, "type_id", None),
                    "device_id": getattr(device, "id", None),
                    "state": getattr(device, "state", None),
                },
            }
        ],
    },
}


def _get_state_value(device, states: dict, state_key: str, fallback=None):
    """Get state value from API states or fallback to device attribute."""
    device_id = getattr(device, "id", None) or getattr(device, "device_id", None)
    if device_id and states and device_id in states:
        device_states = states[device_id]
        if isinstance(device_states, dict) and state_key in device_states:
            return device_states[state_key]
    return fallback


def _get_battery_capacity_value(device, states: dict):
    """Get battery capacity value with manual specification from states."""
    device_id = getattr(device, "id", None) or getattr(device, "device_id", None)

    # Try to get value from states first
    if device_id and states and device_id in states:
        device_states = states[device_id]
        if isinstance(device_states, dict):
            # Check for specific battery capacity state keys from API
            for key in ["battery_capacity", "capacity", "battery_level", "charge_level"]:
                if key in device_states:
                    value = device_states[key]
                    if value is not None:
                        return value

    # Fallback to device attribute if no state found
    return getattr(device, "capacity", None)


def _get_virtual_device_value(device, states: dict):
    """Get virtual device value from states."""
    state_value = _get_state_value(device, states, "state", fallback=getattr(device, "state", False))
    return "on" if state_value else "off"


class DeviceMapper:
    """Maps API devices to Home Assistant entities."""

    def __init__(self):
        """Initialize device mapper."""
        pass

    def get_device_type(self, device) -> str:
        """Get device type from device object."""
        if hasattr(device, "device_type"):
            return getattr(device, "device_type", "unknown")
        elif hasattr(device, "type"):
            return getattr(device, "type", "unknown")
        elif hasattr(device, "__class__"):
            # Fallback to class name
            class_name = device.__class__.__name__.lower()
            if "master" in class_name or "mst" in class_name:
                return "mst"
            elif "battery" in class_name or "bat" in class_name:
                return "bat"
            elif "virtual" in class_name or "vrt" in class_name:
                return "vrt"

        LOGGER.warning("Could not determine device type for device: %s", device)
        return "unknown"

    def get_entities_for_device(self, device) -> List[Dict[str, Any]]:
        """Get entity configurations for a device."""
        device_type = self.get_device_type(device)

        if device_type not in DEVICE_TYPE_MAPPINGS:
            LOGGER.warning("No mapping found for device type: %s", device_type)
            # Debug log to help users share device information for adding new device support
            LOGGER.debug(
                "Unsupported device details - please share this information to add support: "
                "device_type=%s, device_attributes=%s, device_class=%s",
                device_type,
                {attr: getattr(device, attr, None) for attr in dir(device) if not attr.startswith("_")},
                device.__class__.__name__ if hasattr(device, "__class__") else "Unknown",
            )
            return []

        mapping = DEVICE_TYPE_MAPPINGS[device_type]
        entities = []

        for entity_config in mapping["entities"]:
            entity_data = {
                "device": device,
                "device_type": device_type,
                "platform": mapping["platform"],
                **entity_config,
            }
            entities.append(entity_data)

        return entities

    def get_sensor_entities(self, devices: List) -> List[Dict[str, Any]]:
        """Get all sensor entities from devices."""
        sensor_entities = []

        for device in devices:
            entities = self.get_entities_for_device(device)
            sensor_entities.extend([e for e in entities if e["platform"] == "sensor"])

        return sensor_entities

    def get_switch_entities(self, devices: List) -> List[Dict[str, Any]]:
        """Get all switch entities from devices."""
        switch_entities = []

        for device in devices:
            entities = self.get_entities_for_device(device)
            switch_entities.extend([e for e in entities if e["platform"] == "switch"])

        return switch_entities

    def get_device_info(self, device) -> Dict[str, Any]:
        """Get device info for Home Assistant device registry."""
        device_id = getattr(device, "id", None) or getattr(device, "device_id", None)
        device_name = getattr(device, "name", None) or getattr(device, "device_name", None)
        device_model = getattr(device, "model", None) or getattr(device, "device_model", None)
        device_manufacturer = getattr(device, "manufacturer", None) or "MyLight Systems"

        return {
            "identifiers": {("mylight_systems", str(device_id))} if device_id else None,
            "name": device_name or f"MyLight Device {device_id}",
            "manufacturer": device_manufacturer,
            "model": device_model,
            "sw_version": getattr(device, "firmware_version", None),
        }
