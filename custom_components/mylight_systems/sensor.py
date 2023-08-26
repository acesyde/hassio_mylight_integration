"""Sensor platform for integration_blueprint."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, POWER_KILO_WATT, UnitOfEnergy

from .const import DOMAIN
from .coordinator import (
    MyLightSystemsCoordinatorData,
    MyLightSystemsDataUpdateCoordinator,
)
from .entity import IntegrationMyLightSystemsEntity


@dataclass
class MyLightSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[
        [MyLightSystemsCoordinatorData], int | float | str | None
    ]


@dataclass
class MyLightSensorEntityDescription(
    SensorEntityDescription,
    MyLightSensorRequiredKeysMixin,
):
    """Describes a sensor entity."""


MYLIGHT_SENSORS: tuple[MyLightSensorEntityDescription, ...] = (
    MyLightSensorEntityDescription(
        key="total_solar_production",
        name="Solar power production",
        icon="mdi:solar-panel",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.produced_energy.value / 36e2, 2)
        if data.produced_energy is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_consumption",
        name="Total power consumption from the grid with virtual battery",
        icon="mdi:transmission-tower-import",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.grid_energy.value / 36e2, 2)
        if data.grid_energy is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_grid_without_battery_consumption",
        name="Grid power consumption",
        icon="mdi:transmission-tower-import",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(
            data.grid_energy_without_battery.value / 36e2, 2
        )
        if data.grid_energy_without_battery is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_autonomy_rate",
        name="Total autonomy rate",
        icon="mdi:percent-box",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.autonomy_rate.value, 2)
        if data.autonomy_rate is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_self_conso",
        name="Total self consumption",
        icon="mdi:percent-box",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.self_conso.value, 2)
        if data.self_conso is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_charge",
        name="Battery Charge",
        icon="mdi:battery-high",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.msb_charge.value / 36e2, 2)
        if data.msb_charge is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_msb_discharge",
        name="Battery Discharge",
        icon="mdi:battery-low",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.msb_discharge.value / 36e2, 2)
        if data.msb_discharge is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="total_green_energy",
        name="Green energy",
        icon="mdi:solar-panel",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.green_energy.value / 36e2, 2)
        if data.green_energy is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="battery_state",
        name="Battery state",
        icon="mdi:battery",
        native_unit_of_measurement=POWER_KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.battery_state.value / 36e2 / 1e3, 2)
        if data.battery_state is not None
        else 0,
    ),
    MyLightSensorEntityDescription(
        key="grid_returned_energy",
        name="Grid returned energy",
        icon="mdi:transmission-tower-export",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: _calculate_grid_returned_energy(data)

    ),
)


def _calculate_grid_returned_energy(data):
    """Calculate grid returned energy."""

    # Energy produced by the solar panels
    produced_energy = round(data.produced_energy.value / 36e2, 2) if data.produced_energy.value is not None else 0

    # Energy consumed from the solar panels
    green_energy = round(data.green_energy.value / 36e2, 2) if data.green_energy.value is not None else 0

    # Virtual battery charge
    msb_charge = round(data.msb_charge.value / 36e2, 2) if data.msb_charge.value is not None else 0
    result = produced_energy - green_energy - msb_charge
    if result > 0:
        return result
    else:
        return 0


async def async_setup_entry(hass, entry, async_add_devices):
    """Configure sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
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
        entity_description: SensorEntityDescription,
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
