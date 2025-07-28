"""Sensor platform for mylight_systems."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN, LOGGER
from .coordinator import MyLightSystemsDataUpdateCoordinator
from .entity import MyLightSystemsSensorEntity

# Mapping of sensor measure types to Home Assistant sensor configurations
SENSOR_TYPE_MAPPING = {
    "electric_power": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "Power",
    },
    "produced_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Produced Energy",
    },
    "electricity_meter_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Grid Energy",
    },
    "total_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Total Energy",
    },
    "green_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Green Energy",
    },
    "grid_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Grid Energy Consumed",
    },
    "charge_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Charge Energy",
    },
    "discharge_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Discharge Energy",
    },
    "loss_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Loss Energy",
    },
    "soc": {
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "State of Charge",
    },
    "autonomy_rate": {
        "device_class": None,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "Autonomy Rate",
    },
    "selfconso": {
        "device_class": None,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "Self Consumption",
    },
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up MyLight Systems sensor entities."""
    coordinator: MyLightSystemsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []

    # Create sensor entities for each device's sensor states
    if coordinator.data and coordinator.data.states:
        for device_state in coordinator.data.states:
            device_id = device_state.device_id

            # Find the corresponding device to get its name
            device = None
            for dev in coordinator.data.devices:
                if dev.id == device_id:
                    device = dev
                    break

            if not device:
                LOGGER.warning("Device %s not found for device state", device_id)
                continue

            # Create sensor entities for each sensor state
            for sensor_state in device_state.sensor_states:
                sensor_id = sensor_state.sensor_id
                measure_type = sensor_state.measure.type if sensor_state.measure else None

                if measure_type in SENSOR_TYPE_MAPPING:
                    entities.append(
                        MyLightSystemsSensor(
                            coordinator=coordinator,
                            device_id=device_id,
                            sensor_id=sensor_id,
                            sensor_config=SENSOR_TYPE_MAPPING[measure_type],
                        )
                    )
                else:
                    # Create a generic sensor for unknown types
                    LOGGER.info(
                        "Creating generic sensor for unknown type: %s (sensor: %s)",
                        measure_type,
                        sensor_id,
                    )
                    entities.append(
                        MyLightSystemsSensor(
                            coordinator=coordinator,
                            device_id=device_id,
                            sensor_id=sensor_id,
                            sensor_config={
                                "device_class": None,
                                "unit": sensor_state.measure.unit if sensor_state.measure else None,
                                "state_class": SensorStateClass.MEASUREMENT,
                                "name_suffix": f"Sensor {sensor_id.split('-')[-1]}",
                            },
                        )
                    )

    LOGGER.info("Setting up %d sensor entities", len(entities))
    async_add_entities(entities, update_before_add=True)


class MyLightSystemsSensor(MyLightSystemsSensorEntity, SensorEntity):
    """MyLight Systems sensor entity."""

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        device_id: str,
        sensor_id: str,
        sensor_config: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, sensor_id)

        self._sensor_config = sensor_config
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_state_class = sensor_config.get("state_class")

        # Set the entity name
        device_name = self._device.name if self._device else device_id
        sensor_name = sensor_config.get("name_suffix", sensor_id)
        self._attr_name = f"{device_name} {sensor_name}"

    @property
    def native_value(self) -> float | int | None:
        """Return the state of the sensor."""
        sensor_state = self._get_current_sensor_state()
        if not sensor_state or not sensor_state.measure:
            return None

        value = sensor_state.measure.value

        # Convert Ws (watt-seconds) to Wh (watt-hours) for energy sensors
        if sensor_state.measure.unit == "Ws" and self._attr_native_unit_of_measurement == UnitOfEnergy.WATT_HOUR:
            return round(value / 3600, 2)  # Convert Ws to Wh

        return value

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return additional state attributes."""
        sensor_state = self._get_current_sensor_state()
        if not sensor_state or not sensor_state.measure:
            return None

        return {
            "sensor_id": self._sensor_id,
            "measure_type": sensor_state.measure.type,
            "original_unit": sensor_state.measure.unit,
            "last_updated": sensor_state.measure.date,
        }
