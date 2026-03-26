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
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
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
        green_energy=Measure(type="abcd", value=1800, unit="kwh"),
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
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
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(type="abcd", value=1800, unit="kwh"),
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
        green_energy=Measure(type="abcd", value=800, unit="kwh"),
        produced_energy=Measure(type="abcd", value=3600, unit="kwh"),
        grid_energy_without_battery=None,
        msb_charge=Measure(type="abcd", value=700, unit="kwh"),
        msb_discharge=None,
        self_conso=None,
        autonomy_rate=None,
        battery_state=None,
        master_relay_state=None,
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
    """Test with missing green_energy or msb_charge should return None."""
    # Given
    data = produced_energy_only_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert result is None


def test_calculate_grid_returned_energy__should_return_none_when_msb_charge_is_none(
    produced_and_green_energy_data,
):
    """Test with missing msb_charge should return None."""
    # Given
    data = produced_and_green_energy_data

    # When
    result = _calculate_grid_returned_energy(data)

    # Then
    assert result is None


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
    # (3600 - 800 - 700) / 3600 = 0.583333... → rounded to 0.58
    assert 0.58 == result
