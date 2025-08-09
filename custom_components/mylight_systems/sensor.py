"""Sensor platform for mylight_systems."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_SUBSCRIPTION_ID, DATA_COORDINATOR, DOMAIN, LOGGER, NAME
from .coordinator import MyLightSystemsDataUpdateCoordinator

# Mapping of sensor keys to their corresponding total_measures type
TOTAL_MEASURES_MAPPING = {
    "produced_energy": "produced_energy",
    "electricity_meter_energy": "electricity_meter_energy",
    "green_energy": "green_energy",
    "grid_energy": "grid_energy",
    "autonomy_rate": "autonomy_rate",
    "selfconso": "self_conso",
    "discharge_energy": "msb_discharge",
    "loss_energy": "msb_loss",
    "charge_energy": "msb_charge",
}

# Mapping of sensor measure types to Home Assistant sensor entity descriptions
SENSOR_TYPE_MAPPING = {
    "electric_power": SensorEntityDescription(
        key="electric_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        name="Power",
    ),
    "produced_energy": SensorEntityDescription(
        key="produced_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Produced Energy",
    ),
    "electricity_meter_energy": SensorEntityDescription(
        key="electricity_meter_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        name="Grid Energy",
    ),
    "total_energy": SensorEntityDescription(
        key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        name="Total Energy",
    ),
    "green_energy": SensorEntityDescription(
        key="green_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Green Energy",
    ),
    "grid_energy": SensorEntityDescription(
        key="grid_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Grid Energy Consumed",
    ),
    "charge_energy": SensorEntityDescription(
        key="charge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Charge Energy",
    ),
    "discharge_energy": SensorEntityDescription(
        key="discharge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Discharge Energy",
    ),
    "loss_energy": SensorEntityDescription(
        key="loss_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        name="Loss Energy",
    ),
    "soc": SensorEntityDescription(
        key="soc",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        name="State of Charge",
    ),
    "autonomy_rate": SensorEntityDescription(
        key="autonomy_rate",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.TOTAL,
        name="Autonomy Rate",
    ),
    "selfconso": SensorEntityDescription(
        key="selfconso",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.TOTAL,
        name="Self Consumption",
    ),
}


def _find_device_by_id(devices: list, device_id: str):
    """Find device by ID in devices list."""
    for device in devices:
        if device.id == device_id:
            return device
    return None


def _infer_measure_type_from_sensor_id(sensor_id: str) -> str | None:
    """Infer measure type from sensor ID when type is missing."""
    if "autonomy_rate" in sensor_id:
        LOGGER.debug("Inferred measure type 'autonomy_rate' for sensor %s", sensor_id)
        return "autonomy_rate"
    elif "selfconso" in sensor_id:
        LOGGER.debug("Inferred measure type 'selfconso' for sensor %s", sensor_id)
        return "selfconso"
    return None


def _create_generic_sensor_description(sensor_id: str, sensor_state) -> SensorEntityDescription:
    """Create a generic sensor description for unknown sensor types."""
    return SensorEntityDescription(
        key=f"generic_{sensor_id}",
        device_class=None,
        native_unit_of_measurement=sensor_state.measure.unit if sensor_state.measure else None,
        state_class=SensorStateClass.MEASUREMENT,
        name=f"Sensor {sensor_id.split('-')[-1].lower()}",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up MyLight Systems sensor entities."""
    coordinator: MyLightSystemsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []

    # Create sensor entities for each device's sensor states
    if coordinator.data and coordinator.data.states:
        for device_state in coordinator.data.states:
            device_id = device_state.device_id
            device = _find_device_by_id(coordinator.data.devices, device_id)

            if not device:
                LOGGER.warning("Device %s not found for device state", device_id)
                continue

            # Create sensor entities for each sensor state
            for sensor_state in device_state.sensor_states:
                sensor_id = sensor_state.sensor_id
                measure_type = sensor_state.measure.type if sensor_state.measure else None

                # Handle cases where type is missing but can be inferred from sensor ID
                if measure_type is None and sensor_state.measure:
                    measure_type = _infer_measure_type_from_sensor_id(sensor_id)

                if measure_type in SENSOR_TYPE_MAPPING:
                    entities.append(
                        MyLightSystemsSensor(
                            coordinator=coordinator,
                            device_id=device_id,
                            sensor_id=sensor_id,
                            description=SENSOR_TYPE_MAPPING[measure_type],
                        )
                    )
                else:
                    # Create a generic sensor for unknown types
                    LOGGER.info(
                        "Creating generic sensor for unknown type: %s (sensor: %s)",
                        measure_type,
                        sensor_id,
                    )
                    generic_description = _create_generic_sensor_description(sensor_id, sensor_state)
                    entities.append(
                        MyLightSystemsSensor(
                            coordinator=coordinator,
                            device_id=device_id,
                            sensor_id=sensor_id,
                            description=generic_description,
                        )
                    )

    LOGGER.info("Setting up %d sensor entities", len(entities))
    async_add_entities(entities, update_before_add=True)


class MyLightSystemsSensor(CoordinatorEntity[MyLightSystemsDataUpdateCoordinator], SensorEntity):
    """MyLight Systems sensor entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        device_id: str,
        sensor_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._device_id = device_id
        self._sensor_id = sensor_id

        # Get subscription_id from config entry and convert all components to lowercase
        subscription_id = coordinator.config_entry.data[CONF_SUBSCRIPTION_ID]
        self._attr_unique_id = f"{str(subscription_id).lower()}_{device_id.lower().replace('-', '_')}_{sensor_id.lower().replace('-', '_')}"

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
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._device is not None
            and getattr(self._device, "state", True)
            and self._get_current_sensor_state() is not None
        )

    def _get_total_measure_value(self) -> float | int | None:
        """Get value from total_measures if this sensor has a mapping."""
        if not self.coordinator.data or not self.coordinator.data.total_measures:
            return None

        # Check if this sensor key has a mapping to total_measures
        sensor_key = self.entity_description.key
        if sensor_key not in TOTAL_MEASURES_MAPPING:
            return None

        total_measure_type = TOTAL_MEASURES_MAPPING[sensor_key]

        # total_measures is a dict, get the measure by type
        if total_measure_type in self.coordinator.data.total_measures:
            measure = self.coordinator.data.total_measures[total_measure_type]
            return measure.value if hasattr(measure, "value") else measure

        return None

    @property
    def native_value(self) -> float | int | None:
        """Return the state of the sensor."""
        # First try to get value from total_measures if this sensor has a mapping
        total_measure_value = self._get_total_measure_value()
        if total_measure_value is not None:
            value = total_measure_value
            unit = None

            # Get unit from total_measures if available
            sensor_key = self.entity_description.key
            if sensor_key in TOTAL_MEASURES_MAPPING:
                total_measure_type = TOTAL_MEASURES_MAPPING[sensor_key]
                if (
                    self.coordinator.data
                    and self.coordinator.data.total_measures
                    and total_measure_type in self.coordinator.data.total_measures
                ):
                    measure = self.coordinator.data.total_measures[total_measure_type]
                    unit = measure.unit if hasattr(measure, "unit") else None
        else:
            # Fallback to sensor state value
            sensor_state = self._get_current_sensor_state()
            if not sensor_state or not sensor_state.measure:
                return None

            value = sensor_state.measure.value
            unit = sensor_state.measure.unit

        # Convert Ws (watt-seconds) to Wh (watt-hours) for energy sensors
        if unit == "Ws" and self.entity_description.native_unit_of_measurement == UnitOfEnergy.WATT_HOUR:
            value = value / 3600  # Convert Ws to Wh

        # Ensure certain sensors always return positive values
        if self.entity_description.key == "grid_energy" and value is not None and value < 0:
            value = abs(value)

        # Round the final value if it's a float
        if isinstance(value, float):
            return round(value, 2)

        return value

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return additional state attributes."""
        # Check if this sensor uses total_measures
        sensor_key = self.entity_description.key
        uses_total_measures = sensor_key in TOTAL_MEASURES_MAPPING

        if uses_total_measures:
            # Get data from total_measures
            total_measure_type = TOTAL_MEASURES_MAPPING[sensor_key]
            if (
                self.coordinator.data
                and self.coordinator.data.total_measures
                and total_measure_type in self.coordinator.data.total_measures
            ):
                measure = self.coordinator.data.total_measures[total_measure_type]
                return {
                    "sensor_id": self._sensor_id.lower(),
                    "measure_type": total_measure_type,
                    "original_unit": measure.unit if hasattr(measure, "unit") else None,
                    "data_source": "total_measures",
                }

        # Fallback to sensor state
        sensor_state = self._get_current_sensor_state()
        if not sensor_state or not sensor_state.measure:
            return None

        # Get measure type, infer from sensor ID if missing
        measure_type = sensor_state.measure.type
        if measure_type is None:
            if "autonomy_rate" in self._sensor_id:
                measure_type = "autonomy_rate"
            elif "selfconso" in self._sensor_id:
                measure_type = "selfconso"

        return {
            "sensor_id": self._sensor_id.lower(),
            "measure_type": measure_type,
            "original_unit": sensor_state.measure.unit,
            "last_updated": sensor_state.measure.date,
            "data_source": "sensor_states",
        }
