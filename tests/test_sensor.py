"""Unit tests for sensor module."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower

from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import (
    GRID_POWER_SENSORS,
    MYLIGHT_SENSORS,
    MyLightElectricPowerCapacitySensor,
    _calculate_grid_returned_energy,
    async_setup_entry,
)


@pytest.fixture
def none_data():
    """Create coordinator data with all None values."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=None,
        produced_energy=None,
        grid_energy_without_battery=None,
        msb_charge=None,
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
        water_heater_energy=None,
        grid_power=None,
    )


@pytest.fixture
def produced_energy_only_data():
    """Create coordinator data with only produced energy."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=None,
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=None,
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
        water_heater_energy=None,
        grid_power=None,
    )


@pytest.fixture
def produced_and_green_energy_data():
    """Create coordinator data with produced and green energy."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=Measure(type="abcd", value=1800, unit="kwh"),
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=None,
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
        water_heater_energy=None,
        grid_power=None,
    )


@pytest.fixture
def produced_and_msb_charge_data():
    """Create coordinator data with produced energy and MSB charge."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=None,
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(type="abcd", value=1800, unit="kwh"),
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
        water_heater_energy=None,
        grid_power=None,
    )


@pytest.fixture
def all_energy_sources_data():
    """Create coordinator data with all energy sources."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=Measure(type="abcd", value=800, unit="kwh"),
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(type="abcd", value=700, unit="kwh"),
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
        water_heater_energy=None,
        grid_power=None,
    )


def test_calculate_grid_returned_energy__should_return_none_when_all_data_is_none(none_data):
    """Test with None data should return None."""
    # Given
    data = none_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert result is None


def test_calculate_grid_returned_energy__should_return_none_when_green_energy_is_none(produced_energy_only_data):
    """Test with missing green_energy should return None."""
    # Given
    data = produced_energy_only_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert result is None


def test_calculate_grid_returned_energy__should_return_calculated_energy_without_battery(
    produced_and_green_energy_data,
):
    """Test without a smart battery (msb_charge=None) should treat battery charge as 0."""
    # Given
    data = produced_and_green_energy_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    # produced=3600Ws, green=1800Ws, msb_charge=None→0: (3600 - 1800 - 0) / 3600 = 0.5 Wh
    assert pytest.approx(0.5) == result


def test_calculate_grid_returned_energy__should_return_none_when_produced_energy_is_none(
    produced_and_msb_charge_data,
):
    """Test with missing green_energy should return None."""
    # Given - produced_and_msb_charge_data has green_energy=None
    data = produced_and_msb_charge_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert result is None


def test_calculate_grid_returned_energy__should_return_calculated_energy_when_all_sources(all_energy_sources_data):
    """Test with all energy sources should return calculated remaining energy."""
    # Given
    data = all_energy_sources_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    # (3600 - 800 - 700) / 3600 = 0.5833... — raw value, display precision handled by suggested_display_precision=2
    assert pytest.approx(2100 / 3600) == result


def _water_heater_value_fn(data):
    """Return the value_fn for the water_heater_energy sensor."""
    return next(s for s in MYLIGHT_SENSORS if s.key == "water_heater_energy").value_fn(data)


def test_water_heater_energy__should_return_none_when_measure_is_absent(none_data):
    """Test that value_fn returns None when water_heater_energy is not in the API response."""
    assert _water_heater_value_fn(none_data) is None


def test_water_heater_energy__should_return_wh_value_when_measure_is_present(none_data):
    """Test that value_fn converts Ws to Wh correctly."""
    # Given
    data = none_data._replace(water_heater_energy=Measure(type="water_heater_energy", value=3600, unit="Ws"))

    # When
    result = _water_heater_value_fn(data)

    # Then — 3600 Ws / 3600 = 1.0 Wh
    assert pytest.approx(1.0) == result


def _build_capacity_sensor(value: float) -> MyLightElectricPowerCapacitySensor:
    """Build a MyLightElectricPowerCapacitySensor with a mocked coordinator."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    return MyLightElectricPowerCapacitySensor(entry_id="test_entry", coordinator=coordinator, value=value)


def test_electric_power_capacity_sensor__exposes_native_value():
    """Test that the static sensor exposes the value passed at construction."""
    sensor = _build_capacity_sensor(9.0)

    assert sensor.native_value == 9.0
    assert sensor.native_unit_of_measurement == "kVA"
    assert sensor.device_class == SensorDeviceClass.APPARENT_POWER
    assert sensor.available is True
    assert sensor.unique_id == "test_entry_electric_power_capacity"


def _grid_value_fn(key, data):
    """Return the value_fn result of a grid power sensor."""
    return next(s for s in GRID_POWER_SENSORS if s.key == key).value_fn(data)


@pytest.mark.parametrize(
    ("power", "signed", "imported", "exported"),
    [(1500, 1500, 1500, 0), (-1500, -1500, 0, 1500), (0, 0, 0, 0)],
)
def test_grid_power_sensors__should_split_signed_power(none_data, power, signed, imported, exported):
    """Signed power maps to import (positive part) and export (negative part); zero stays zero."""
    data = none_data._replace(grid_power=Measure(type="electric_power", value=power, unit="watt"))

    assert signed == _grid_value_fn("grid_power", data)
    assert imported == _grid_value_fn("grid_import_power", data)
    assert exported == _grid_value_fn("grid_export_power", data)


@pytest.mark.parametrize("key", ["grid_power", "grid_import_power", "grid_export_power"])
def test_grid_power_sensors__should_be_unknown_without_measure(none_data, key):
    """Missing data is None, never 0."""
    assert _grid_value_fn(key, none_data) is None


def test_grid_power_sensors__should_declare_power_measurement():
    """All three are measured watt power sensors."""
    for description in GRID_POWER_SENSORS:
        assert SensorDeviceClass.POWER == description.device_class
        assert SensorStateClass.MEASUREMENT == description.state_class
        assert UnitOfPower.WATT == description.native_unit_of_measurement


@pytest.mark.asyncio
@pytest.mark.parametrize(("meter_id", "expected"), [("meter-1", 3), (None, 0)])
async def test_setup_entry__should_create_grid_power_sensors_only_when_meter_found(meter_id, expected):
    """The three grid power sensors exist only when a single meter was discovered."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {}
    entry.runtime_data.grid_meter_id = meter_id
    add = MagicMock()

    await async_setup_entry(MagicMock(), entry, add)

    keys = {"grid_power", "grid_import_power", "grid_export_power"}
    created = [e for e in add.call_args.args[0] if e.entity_description.key in keys]
    assert expected == len(created)
