# Device to Entity Mappings

This document describes how devices from the MyLight Systems API are mapped to Home Assistant entities.

## Overview

The MyLight Systems integration uses a device mapper (`device_mapper.py`) to convert API devices into appropriate Home Assistant entities. The mapper analyzes each device and creates sensors and switches based on the device type and capabilities.

## Device Types and Entity Mappings

### Master Device (`mst`)

**Platform**: Sensor

**Entities**:
- **Master Device** (`master_device`)
  - Icon: `mdi:power-plug`
  - Name: Uses device name (e.g., "Master")
  - Maps to: `device.state`
  - **Attributes**:
    - `device_type_name`: Device type description
    - `report_period`: Reporting period in seconds
    - `type_id`: Device type identifier
    - `device_id`: Device ID

## Device Type Detection

The device mapper uses the following logic to determine device types:

1. **Primary**: Check for `device.device_type` attribute
2. **Secondary**: Check for `device.type` attribute
3. **Fallback**: Analyze class name for keywords:
   - `master` or `mst` → `mst`

## Entity Naming Convention

Entities are named using the following pattern:
```
{device_name} {entity_name} ({device_id})
```

Examples:
- `Master (F8DFE101A81C)` - for mst devices using device name

## Device Information

Each entity includes device information for the Home Assistant device registry:

- **Identifiers**: `("mylight_systems", device_id)`
- **Name**: Device name or fallback to "MyLight Device {device_id}"
- **Manufacturer**: "MyLight Systems" (or from device.manufacturer)
- **Model**: From `device.model` or `device.device_model`
- **Software Version**: From `device.firmware_version`

## Adding New Device Types

To add support for a new device type:

1. **Add mapping to `DEVICE_TYPE_MAPPINGS`** in `device_mapper.py`:
   ```python
   "new_device_type": {
       "platform": "sensor",  # or "switch"
       "entities": [
           {
               "key": "entity_key",
               "name": "Entity Name",
               "icon": "mdi:icon-name",
               "unit_of_measurement": UnitOfMeasurement.UNIT,
               "device_class": SensorDeviceClass.CLASS,
               "state_class": SensorStateClass.CLASS,
               "value_fn": lambda device: getattr(device, "attribute", 0)
           }
       ]
   }
   ```

2. **Update device type detection** in `get_device_type()` method

3. **Update this documentation** with the new device type and entities

## Troubleshooting

### No Entities Created
- Check that `get_devices()` returns devices from the API
- Verify device type detection is working correctly
- Check logs for mapping warnings

### Missing Device Attributes
- The mapper uses `getattr()` with defaults to handle missing attributes
- Devices without expected attributes will return default values (usually 0 or "unknown")

### Entity Not Updating
- Ensure the `value_fn` accesses the correct device attribute
- Check that the coordinator is successfully refreshing device data 
