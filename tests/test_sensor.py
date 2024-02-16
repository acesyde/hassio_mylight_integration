from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import _calculate_grid_returned_energy


def test_calculate_grid_returned_energy_with_none_data_should_return_0():
    # Arrange
    data = MyLightSystemsCoordinatorData(
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

    # Act

    result = _calculate_grid_returned_energy(data)

    # Assert

    assert result == 0


def test_calculate_grid_returned_energy_with_produced_energy_should_return_produced_energy():
    # Arrange
    data = MyLightSystemsCoordinatorData(
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

    # Act

    result = _calculate_grid_returned_energy(data)

    # Assert

    assert result == 1.0


def test_calculate_grid_returned_energy_with_produced_and_green_return():
    # Arrange
    data = MyLightSystemsCoordinatorData(
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

    # Act

    result = _calculate_grid_returned_energy(data)

    # Assert

    assert result == 0.5


def test_calculate_grid_returned_energy_with_produced_and_msb_charge_return():
    # Arrange
    data = MyLightSystemsCoordinatorData(
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

    # Act

    result = _calculate_grid_returned_energy(data)

    # Assert

    assert result == 0.5

def test_calculate_grid_returned_energy_with_all_return():
    # Arrange
    data = MyLightSystemsCoordinatorData(
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

    # Act

    result = _calculate_grid_returned_energy(data)

    # Assert

    assert result == 0.59
