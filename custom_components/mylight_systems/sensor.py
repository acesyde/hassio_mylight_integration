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
from homeassistant.const import PERCENTAGE, UnitOfEnergy

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
        name="Total solar power production",
        icon="mdi:solar-panel",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.produced_energy.value / 36e5, 2),
    ),
    MyLightSensorEntityDescription(
        key="total_grid_consumption",
        name="Total power consumption from the grid",
        icon="mdi:transmission-tower",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: round(data.grid_energy.value / 36e5, 2),
    ),
    MyLightSensorEntityDescription(
        key="total_autonomy_rate",
        name="Total autonomy rate",
        icon="mdi:percent-box",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        value_fn=lambda data: data.autonomy_rate.value,
    ),
    MyLightSensorEntityDescription(
        key="total_self_conso",
        name="Total self consumption",
        icon="mdi:percent-box",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        value_fn=lambda data: data.self_conso.value,
    ),
)


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
