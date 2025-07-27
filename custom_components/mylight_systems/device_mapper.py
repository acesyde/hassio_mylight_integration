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
        # Add sensor state mappings for MySmartBattery devices (devices with _msb suffix)
        "sensor_state_mappings": {
            "charge_energy": {
                "key": "charge_energy",
                "name": lambda device: f"{getattr(device, 'name', 'Battery')} Charge Energy",
                "icon": "mdi:battery-plus",
                "device_class": "energy",
                "state_class": "total_increasing",
                "unit_of_measurement": "Wh",
                "value_conversion": lambda value: value / 3600 if value is not None else None,  # Convert Ws to Wh
            },
            "discharge_energy": {
                "key": "discharge_energy",
                "name": lambda device: f"{getattr(device, 'name', 'Battery')} Discharge Energy",
                "icon": "mdi:battery-minus",
                "device_class": "energy",
                "state_class": "total_increasing",
                "unit_of_measurement": "Wh",
                "value_conversion": lambda value: value / 3600 if value is not None else None,  # Convert Ws to Wh
            },
            "loss_energy": {
                "key": "loss_energy",
                "name": lambda device: f"{getattr(device, 'name', 'Battery')} Energy Loss",
                "icon": "mdi:battery-alert",
                "device_class": "energy",
                "state_class": "total_increasing",
                "unit_of_measurement": "Wh",
                "value_conversion": lambda value: value / 3600 if value is not None else None,  # Convert Ws to Wh
            },
            "soc": {
                "key": "soc",
                "name": lambda device: f"{getattr(device, 'name', 'Battery')} State of Charge",
                "icon": "mdi:battery",
                "device_class": "energy",
                "state_class": "measurement",
                "unit_of_measurement": "Wh",
                "value_conversion": lambda value: value / 3600 if value is not None else None,  # Convert Ws to Wh
            },
        },
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
    """Get battery capacity value from device capacity attribute."""
    return getattr(device, "capacity", None)


def _get_virtual_device_value(device, states: dict):
    """Get virtual device value from states."""
    state_value = _get_state_value(device, states, "state", fallback=getattr(device, "state", False))
    return "on" if state_value else "off"


def _get_sensor_state_value(device, states: dict, sensor_type: str, value_conversion=None):
    """Get sensor state value from API states."""
    device_id = getattr(device, "id", None) or getattr(device, "device_id", None)
    if not device_id or not states:
        return None

    # Look for device states in the states data
    # The states can be in different formats depending on how the coordinator processes them
    device_states = None

    # Check if it's the processed coordinator format (dict with device_id keys)
    if isinstance(states, dict) and device_id in states:
        device_states = states[device_id]

    # If not found, look for deviceStates array (raw API format or list of objects)
    elif isinstance(states, dict) and "deviceStates" in states:
        device_states_list = states["deviceStates"]
        if isinstance(device_states_list, list):
            for device_state in device_states_list:
                # Handle both dict and object formats
                device_state_id = (
                    getattr(device_state, "deviceId", None)
                    if hasattr(device_state, "deviceId")
                    else device_state.get("deviceId", None)
                    if hasattr(device_state, "get")
                    else None
                )
                if device_state_id == device_id:
                    device_states = device_state
                    break

    # Direct list format (list of device states)
    elif isinstance(states, list):
        for device_state in states:
            # Handle both dict and object formats
            device_state_id = (
                getattr(device_state, "deviceId", None)
                if hasattr(device_state, "deviceId")
                else device_state.get("deviceId", None)
                if hasattr(device_state, "get")
                else None
            )
            if device_state_id == device_id:
                device_states = device_state
                break

    if not device_states:
        return None

    # Get sensor states - handle both dict and object formats
    sensor_states = None
    if hasattr(device_states, "sensorStates"):
        sensor_states = getattr(device_states, "sensorStates", None)
    elif hasattr(device_states, "get") and "sensorStates" in device_states:
        sensor_states = device_states["sensorStates"]

    if not sensor_states:
        return None

    # Look for the specific sensor type
    sensor_id_suffix = f"-{sensor_type}"
    for sensor_state in sensor_states:
        # Handle both dict and object formats for sensor_state
        sensor_id = (
            getattr(sensor_state, "sensorId", None)
            if hasattr(sensor_state, "sensorId")
            else sensor_state.get("sensorId", None)
            if hasattr(sensor_state, "get")
            else None
        )

        if sensor_id and sensor_id.endswith(sensor_id_suffix):
            # Get the measure - handle both dict and object formats
            measure = None
            if hasattr(sensor_state, "measure"):
                measure = getattr(sensor_state, "measure", None)
            elif hasattr(sensor_state, "get") and "measure" in sensor_state:
                measure = sensor_state["measure"]

            if measure:
                # Get the value - handle both dict and object formats
                value = None
                if hasattr(measure, "value"):
                    value = getattr(measure, "value", None)
                elif hasattr(measure, "get") and "value" in measure:
                    value = measure["value"]

                # Apply value conversion if provided
                if value is not None and value_conversion and callable(value_conversion):
                    return value_conversion(value)

                return value

    return None


def _is_msb_device(device) -> bool:
    """Check if device is a MySmartBattery device."""
    device_id = getattr(device, "id", None) or getattr(device, "device_id", None)
    return device_id and device_id.endswith("_msb")


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

        # Add regular device-level entities
        for entity_config in mapping["entities"]:
            entity_data = {
                "device": device,
                "device_type": device_type,
                "platform": mapping["platform"],
                **entity_config,
            }
            entities.append(entity_data)

        # Add sensor state entities for MySmartBattery devices
        if device_type == "bat" and _is_msb_device(device) and "sensor_state_mappings" in mapping:
            for sensor_type, sensor_config in mapping["sensor_state_mappings"].items():
                entity_data = {
                    "device": device,
                    "device_type": device_type,
                    "platform": mapping["platform"],
                    "key": sensor_config["key"],
                    "name": sensor_config["name"],
                    "icon": sensor_config.get("icon"),
                    "device_class": sensor_config.get("device_class"),
                    "state_class": sensor_config.get("state_class"),
                    "unit_of_measurement": sensor_config.get("unit_of_measurement"),
                    "value_fn": lambda device,
                    states,
                    st=sensor_type,
                    vc=sensor_config.get("value_conversion"): _get_sensor_state_value(device, states, st, vc),
                    "attributes_fn": lambda device: {
                        "device_type_name": getattr(device, "device_type_name", None),
                        "type_id": getattr(device, "type_id", None),
                        "device_id": getattr(device, "id", None),
                        "sensor_type": sensor_type,
                    },
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
