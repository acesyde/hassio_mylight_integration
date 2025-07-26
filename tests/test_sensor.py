"""Unit tests for sensor module."""

import pytest

from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import _calculate_grid_returned_energy


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
    )


@pytest.fixture
def produced_energy_only_data():
    """Create coordinator data with only produced energy."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=None,
        produced_energy=Measure(key="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=None,
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
    )


@pytest.fixture
def produced_and_green_energy_data():
    """Create coordinator data with produced and green energy."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=Measure(key="abcd", value=1800, unit="kwh"),
        produced_energy=Measure(key="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=None,
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
    )


@pytest.fixture
def produced_and_msb_charge_data():
    """Create coordinator data with produced energy and MSB charge."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=None,
        produced_energy=Measure(key="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(key="abcd", value=1800, unit="kwh"),
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
    )


@pytest.fixture
def all_energy_sources_data():
    """Create coordinator data with all energy sources."""
    return MyLightSystemsCoordinatorData(
        grid_energy=None,
        green_energy=Measure(key="abcd", value=800, unit="kwh"),
        produced_energy=Measure(key="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(key="abcd", value=700, unit="kwh"),
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
    )


def test_calculate_grid_returned_energy__should_return_zero_when_all_data_is_none(none_data):
    """Test with None data should return 0."""
    # Given
    data = none_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert 0 == result


def test_calculate_grid_returned_energy__should_return_full_energy_when_only_produced_energy(produced_energy_only_data):
    """Test with only produced energy should return full produced energy value."""
    # Given
    data = produced_energy_only_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert 1.0 == result


def test_calculate_grid_returned_energy__should_return_half_energy_when_produced_and_green_energy(
    produced_and_green_energy_data,
):
    """Test with produced and green energy should return remaining energy."""
    # Given
    data = produced_and_green_energy_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert 0.5 == result


def test_calculate_grid_returned_energy__should_return_half_energy_when_produced_and_msb_charge(
    produced_and_msb_charge_data,
):
    """Test with produced energy and MSB charge should return remaining energy."""
    # Given
    data = produced_and_msb_charge_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert 0.5 == result


def test_calculate_grid_returned_energy__should_return_calculated_energy_when_all_sources(all_energy_sources_data):
    """Test with all energy sources should return calculated remaining energy."""
    # Given
    data = all_energy_sources_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert 0.59 == result
