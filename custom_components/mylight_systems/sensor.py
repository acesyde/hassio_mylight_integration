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
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
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
        name="Solar power production",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.produced_energy.value / WS_TO_WH, 2) if data.produced_energy is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_consumption",
        name="Total power consumption from the grid with virtual battery",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.grid_energy.value / WS_TO_WH, 2) if data.grid_energy is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_without_battery_consumption",
        name="Grid power consumption",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.grid_energy_without_battery.value / WS_TO_WH, 2)
        if data.grid_energy_without_battery is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_autonomy_rate",
        name="Total autonomy rate",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.autonomy_rate.value, 2) if data.autonomy_rate is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_self_conso",
        name="Total self consumption",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.self_conso.value, 2) if data.self_conso is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_charge",
        name="Battery Charge",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.msb_charge.value / WS_TO_WH, 2) if data.msb_charge is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_discharge",
        name="Battery Discharge",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.msb_discharge.value / WS_TO_WH, 2) if data.msb_discharge is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_green_energy",
        name="Green energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.green_energy.value / WS_TO_WH, 2) if data.green_energy is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="battery_state",
        name="Battery state",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.battery_state.value / WS_TO_WH / W_TO_KW, 2) if data.battery_state is not None else 0,
    ),
    MyLightSensorEntityDescription(
        key="grid_returned_energy",
        name="Grid returned energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=2,
        value_fn=lambda data: _calculate_grid_returned_energy(data),
    ),
)


def _calculate_grid_returned_energy(data: MyLightSystemsCoordinatorData) -> float:
    """Calculate grid returned energy."""
    if data is None:
        return 0

    # Energy produced by the solar panels
    produced_energy = 0

    if data.produced_energy is not None and data.produced_energy.value is not None:
        produced_energy = round(data.produced_energy.value / WS_TO_WH, 2)

    # Energy consumed from the solar panels
    green_energy = 0

    if data.green_energy is not None and data.green_energy.value is not None:
        green_energy = round(data.green_energy.value / WS_TO_WH, 2)

    msb_charge = 0

    # Virtual battery charge
    if data.msb_charge is not None and data.msb_charge.value is not None:
        msb_charge = round(data.msb_charge.value / WS_TO_WH, 2)

    result = round(produced_energy - green_energy - msb_charge, 2)

    if result > 0:
        return result
    else:
        return 0


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
