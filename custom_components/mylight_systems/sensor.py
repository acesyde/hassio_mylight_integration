"""Sensor platform for MyLight Systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MyLightConfigEntry
from .const import DOMAIN
from .coordinator import (
    MyLightSystemsCoordinatorData,
    MyLightSystemsDataUpdateCoordinator,
)
from .entity import IntegrationMyLightSystemsEntity

# Unit conversion constants
WS_TO_WH = 3600  # Watt-seconds to Watt-hours
W_TO_KW = 1000  # Watts to Kilowatts


@dataclass(frozen=True, kw_only=True)
class MyLightSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor entity."""

    value_fn: Callable[[MyLightSystemsCoordinatorData], int | float | str | None]


MYLIGHT_SENSORS: tuple[MyLightSensorEntityDescription, ...] = (
    MyLightSensorEntityDescription(
        key="total_solar_production",
        name="Total solar production",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.produced_energy.value / WS_TO_WH, 2) if data.produced_energy is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_consumption",
        name="Total grid consumption (with virtual battery)",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.grid_energy.value / WS_TO_WH, 2) if data.grid_energy is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_without_battery_consumption",
        name="Total grid consumption (without virtual battery)",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.grid_energy_without_battery.value / WS_TO_WH, 2)
        if data.grid_energy_without_battery is not None
        else None,
    ),
    MyLightSensorEntityDescription(
        key="total_autonomy_rate",
        name="Autonomy rate",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.autonomy_rate.value, 2) if data.autonomy_rate is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_self_conso",
        name="Self-consumption rate",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.self_conso.value, 2) if data.self_conso is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_charge",
        name="Total battery charge",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.msb_charge.value / WS_TO_WH, 2) if data.msb_charge is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_discharge",
        name="Total battery discharge",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.msb_discharge.value / WS_TO_WH, 2) if data.msb_discharge is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="total_green_energy",
        name="Total green energy (direct solar)",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.green_energy.value / WS_TO_WH, 2) if data.green_energy is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="battery_state",
        name="Battery energy stored",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.battery_state.value / WS_TO_WH / W_TO_KW, 2) if data.battery_state is not None else None,
    ),
    MyLightSensorEntityDescription(
        key="grid_returned_energy",
        name="Total grid returned energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: _calculate_grid_returned_energy(data),
    ),
)


def _calculate_grid_returned_energy(data: MyLightSystemsCoordinatorData) -> float | None:
    """Calculate grid returned energy."""
    if (
        data is None
        or data.produced_energy is None
        or data.green_energy is None
        or data.msb_charge is None
    ):
        return None

    produced_energy = round(data.produced_energy.value / WS_TO_WH, 2)
    green_energy = round(data.green_energy.value / WS_TO_WH, 2)
    msb_charge = round(data.msb_charge.value / WS_TO_WH, 2)

    result = round(produced_energy - green_energy - msb_charge, 2)
    return result if result > 0 else 0


async def async_setup_entry(hass: HomeAssistant, entry: MyLightConfigEntry, async_add_devices: AddEntitiesCallback) -> None:
    """Configure sensor platform."""
    coordinator = entry.runtime_data
    async_add_devices(
        MyLightSystemsSensor(
            entry_id=entry.entry_id,
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in MYLIGHT_SENSORS
    )


class MyLightSystemsSensor(IntegrationMyLightSystemsEntity, SensorEntity):
    """MyLightSystems Sensor class."""

    def __init__(
        self,
        entry_id: str,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        entity_description: MyLightSensorEntityDescription,
    ) -> None:
        """Init."""
        super().__init__(coordinator)
        self.entity_id = f"{DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self.entity_description = entity_description

    @property
    def native_value(self) -> int | float | str:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if last update was successful."""
        return self.coordinator.last_update_success
