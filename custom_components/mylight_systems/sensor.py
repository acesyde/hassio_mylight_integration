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
from mylightsystems.models import VirtualDevice

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
    "total_energy": "energy",
    "grid_consumed_without_battery_energy": "grid_sans_msb_energy",
}

# Mapping of sensor measure types to Home Assistant sensor entity descriptions
SENSOR_TYPE_MAPPING = {
    "electric_power": SensorEntityDescription(
        key="electric_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="power",
    ),
    "produced_energy": SensorEntityDescription(
        key="produced_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="produced_energy",
    ),
    "electricity_meter_energy": SensorEntityDescription(
        key="electricity_meter_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="grid_energy_meter",
    ),
    "total_energy": SensorEntityDescription(
        key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_energy",
    ),
    "green_energy": SensorEntityDescription(
        key="green_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="green_energy",
    ),
    "grid_energy": SensorEntityDescription(
        key="grid_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="grid_energy_consumed",
    ),
    "charge_energy": SensorEntityDescription(
        key="charge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="charge_energy",
    ),
    "discharge_energy": SensorEntityDescription(
        key="discharge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="discharge_energy",
    ),
    "loss_energy": SensorEntityDescription(
        key="loss_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="loss_energy",
    ),
    "soc": SensorEntityDescription(
        key="soc",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="state_of_charge",
    ),
    "autonomy_rate": SensorEntityDescription(
        key="autonomy_rate",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.TOTAL,
        translation_key="autonomy_rate",
    ),
    "selfconso": SensorEntityDescription(
        key="selfconso",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.TOTAL,
        translation_key="self_consumption",
    ),
    "grid_returned_energy": SensorEntityDescription(
        key="grid_returned_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="grid_returned_energy",
    ),
    "grid_consumed_without_battery_energy": SensorEntityDescription(
        key="grid_consumed_without_battery_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="grid_consumed_without_battery_energy",
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
                    # Skip creating regular sensors for those handled by custom sensor classes
                    if measure_type == "grid_consumed_without_battery_energy":
                        continue

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

    # Add custom sensors for virtual devices
    if coordinator.data and coordinator.data.devices:
        for device in coordinator.data.devices:
            if isinstance(device, VirtualDevice):
                # Add grid_returned_energy computed sensor
                entities.append(
                    MyLightSystemsGridReturnedEnergySensor(
                        coordinator=coordinator,
                        virtual_device_id=device.id,
                        description=SENSOR_TYPE_MAPPING["grid_returned_energy"],
                    )
                )
                LOGGER.info("Added grid_returned_energy computed sensor for virtual device %s", device.id)

                # Add grid_consumed_without_battery_energy sensor
                entities.append(
                    MyLightSystemsGridConsumedWithoutBatteryEnergySensor(
                        coordinator=coordinator,
                        virtual_device_id=device.id,
                        description=SENSOR_TYPE_MAPPING["grid_consumed_without_battery_energy"],
                    )
                )
                LOGGER.info("Added grid_consumed_without_battery_energy sensor for virtual device %s", device.id)
                break

    LOGGER.info("Setting up %d sensor entities", len(entities))
    async_add_entities(entities, update_before_add=True)


class MyLightSystemsGridReturnedEnergySensor(CoordinatorEntity[MyLightSystemsDataUpdateCoordinator], SensorEntity):
    """Grid Returned Energy computed sensor entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        virtual_device_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the computed sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._virtual_device_id = virtual_device_id

        # Get subscription_id from config entry and convert all components to lowercase
        subscription_id = coordinator.config_entry.data[CONF_SUBSCRIPTION_ID]
        self._attr_unique_id = (
            f"{str(subscription_id).lower()}_{virtual_device_id.lower().replace('-', '_')}_grid_returned_energy"
        )

        # Find the virtual device in coordinator data
        self._device = None
        for device in coordinator.data.devices if coordinator.data else []:
            if device.id == virtual_device_id:
                self._device = device
                break

        if not self._device:
            LOGGER.error("Virtual device %s not found in coordinator data", virtual_device_id)
            return

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, virtual_device_id)},
            name=self._device.name,
            manufacturer=NAME,
            model=self._device.device_type_name,
        )

    def _get_total_measure_value_by_type(self, measure_type: str) -> float:
        """Get value from total_measures by type."""
        if not self.coordinator.data or not self.coordinator.data.total_measures:
            return 0.0

        # Find the measure by type in the total_measures list
        for measure in self.coordinator.data.total_measures:
            if hasattr(measure, "type") and measure.type == measure_type:
                value = measure.value if hasattr(measure, "value") else 0.0
                # Convert Ws to Wh if needed
                unit = measure.unit if hasattr(measure, "unit") else None
                if unit == "Ws":
                    value = value / 3600  # Convert Ws to Wh
                return float(value) if value is not None else 0.0

        return 0.0

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self._device is not None and getattr(self._device, "state", True)
        )

    @property
    def native_value(self) -> float | None:
        """Return the computed grid returned energy value."""
        # Get the three required values with defaults of 0
        produced_energy = self._get_total_measure_value_by_type("produced_energy")
        green_energy = self._get_total_measure_value_by_type("green_energy")
        msb_charge = self._get_total_measure_value_by_type("msb_charge")

        # Compute: round(produced_energy - green_energy - msb_charge, 2)
        result = produced_energy - green_energy - msb_charge
        return round(result, 2)

    @property
    def extra_state_attributes(self) -> dict[str, str | float] | None:
        """Return additional state attributes."""

        return {
            "data_source": "computed_from_total_measures",
        }


class MyLightSystemsGridConsumedWithoutBatteryEnergySensor(
    CoordinatorEntity[MyLightSystemsDataUpdateCoordinator], SensorEntity
):
    """Grid Consumed Without Battery Energy sensor entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        virtual_device_id: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._virtual_device_id = virtual_device_id

        # Get subscription_id from config entry and convert all components to lowercase
        subscription_id = coordinator.config_entry.data[CONF_SUBSCRIPTION_ID]
        self._attr_unique_id = f"{str(subscription_id).lower()}_{virtual_device_id.lower().replace('-', '_')}_grid_consumed_without_battery_energy"

        # Find the virtual device in coordinator data
        self._device = None
        for device in coordinator.data.devices if coordinator.data else []:
            if device.id == virtual_device_id:
                self._device = device
                break

        if not self._device:
            LOGGER.error("Virtual device %s not found in coordinator data", virtual_device_id)
            return

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, virtual_device_id)},
            name=self._device.name,
            manufacturer=NAME,
            model=self._device.device_type_name,
        )

    def _get_total_measure_value_by_type(self, measure_type: str) -> float:
        """Get value from total_measures by type."""
        if not self.coordinator.data or not self.coordinator.data.total_measures:
            return 0.0

        # Find the measure by type in the total_measures list
        for measure in self.coordinator.data.total_measures:
            if hasattr(measure, "type") and measure.type == measure_type:
                value = measure.value if hasattr(measure, "value") else 0.0
                # Convert Ws to Wh if needed
                unit = measure.unit if hasattr(measure, "unit") else None
                if unit == "Ws":
                    value = value / 3600  # Convert Ws to Wh
                return float(value) if value is not None else 0.0

        return 0.0

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self._device is not None and getattr(self._device, "state", True)
        )

    @property
    def native_value(self) -> float | None:
        """Return the grid consumed without battery energy value."""
        # Get the value directly from total_measures using the mapped type
        grid_sans_msb_energy = self._get_total_measure_value_by_type("grid_sans_msb_energy")
        return round(grid_sans_msb_energy, 2) if grid_sans_msb_energy is not None else 0.0

    @property
    def extra_state_attributes(self) -> dict[str, str | float] | None:
        """Return additional state attributes."""
        return {
            "data_source": "total_measures",
            "measure_type": "grid_sans_msb_energy",
        }


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
            LOGGER.debug("Sensor %s has no mapping to total_measures", sensor_key)
            return None

        total_measure_type = TOTAL_MEASURES_MAPPING[sensor_key]
        LOGGER.debug("Total measure type: %s", total_measure_type)

        # total_measures is a list, find the measure by type
        for measure in self.coordinator.data.total_measures:
            if hasattr(measure, "type") and measure.type == total_measure_type:
                LOGGER.debug("Sensor %s has mapping to total_measures", sensor_key)
                value = measure.value if hasattr(measure, "value") else measure
                LOGGER.debug("Measure value: %s", value)
                return value

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
                if self.coordinator.data and self.coordinator.data.total_measures:
                    # Find the measure by type in the list
                    for measure in self.coordinator.data.total_measures:
                        if hasattr(measure, "type") and measure.type == total_measure_type:
                            unit = measure.unit if hasattr(measure, "unit") else None
                            break
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
            if self.coordinator.data and self.coordinator.data.total_measures:
                # Find the measure by type in the list
                for measure in self.coordinator.data.total_measures:
                    if hasattr(measure, "type") and measure.type == total_measure_type:
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
