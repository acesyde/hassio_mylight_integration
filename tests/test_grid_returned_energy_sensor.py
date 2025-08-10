"""Tests for grid returned energy sensor in mylight_systems integration."""

from unittest.mock import Mock

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from mylightsystems.models import VirtualDevice

from custom_components.mylight_systems.const import CONF_SUBSCRIPTION_ID
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import (
    SENSOR_TYPE_MAPPING,
    MyLightSystemsGridReturnedEnergySensor,
)


def _create_mock_coordinator(subscription_id: str = "test123"):
    """Create a mock coordinator for testing."""
    mock_coordinator = Mock()
    mock_coordinator.config_entry = Mock()
    mock_coordinator.config_entry.data = {CONF_SUBSCRIPTION_ID: subscription_id}
    mock_coordinator.last_update_success = True
    return mock_coordinator


def _create_mock_virtual_device(device_id: str = "virtual-device-001"):
    """Create a mock virtual device."""
    mock_virtual_device = Mock(spec=VirtualDevice)
    mock_virtual_device.id = device_id
    mock_virtual_device.name = "Virtual Device"
    mock_virtual_device.device_type_name = "Virtual Battery"
    mock_virtual_device.state = True
    return mock_virtual_device


def _create_mock_total_measures(produced_energy=0.0, green_energy=0.0, msb_charge=0.0, unit="Wh"):
    """Create mock total measures for testing."""
    measures = []

    # Produced energy measure
    produced_measure = Mock()
    produced_measure.type = "produced_energy"
    produced_measure.value = produced_energy
    produced_measure.unit = unit
    measures.append(produced_measure)

    # Green energy measure
    green_measure = Mock()
    green_measure.type = "green_energy"
    green_measure.value = green_energy
    green_measure.unit = unit
    measures.append(green_measure)

    # MSB charge measure
    msb_charge_measure = Mock()
    msb_charge_measure.type = "msb_charge"
    msb_charge_measure.value = msb_charge
    msb_charge_measure.unit = unit
    measures.append(msb_charge_measure)

    return measures


def test_grid_returned_energy_sensor_type_mapping__should_have_correct_config():
    """Test that grid_returned_energy sensor type has correct configuration."""
    # When
    actual_description = SENSOR_TYPE_MAPPING["grid_returned_energy"]

    # Then
    assert actual_description.key == "grid_returned_energy"
    assert actual_description.device_class == SensorDeviceClass.ENERGY
    assert actual_description.native_unit_of_measurement == UnitOfEnergy.WATT_HOUR
    assert actual_description.state_class == SensorStateClass.TOTAL_INCREASING
    assert actual_description.translation_key == "grid_returned_energy"


def test_grid_returned_energy_sensor__should_compute_basic_formula():
    """Test that sensor computes grid returned energy using the formula: produced_energy - green_energy - msb_charge."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    # Set up total measures: 1000 - 300 - 200 = 500
    total_measures = _create_mock_total_measures(produced_energy=1000.0, green_energy=300.0, msb_charge=200.0)

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device], states=[], total_measures=total_measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 500.0  # 1000 - 300 - 200


def test_grid_returned_energy_sensor__should_use_default_values_for_missing_measures():
    """Test that sensor uses 0 as default when measures are missing."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    # Only provide produced_energy measure, others missing
    produced_measure = Mock()
    produced_measure.type = "produced_energy"
    produced_measure.value = 500.0
    produced_measure.unit = "Wh"

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device],
        states=[],
        total_measures=[produced_measure],  # Missing green_energy and msb_charge
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 500.0  # 500 - 0 - 0 (defaults used)


def test_grid_returned_energy_sensor__should_handle_all_defaults_when_no_measures():
    """Test that sensor returns 0 when no total measures are available."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device],
        states=[],
        total_measures=[],  # No measures at all
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 0.0  # 0 - 0 - 0 (all defaults)


def test_grid_returned_energy_sensor__should_handle_negative_result():
    """Test that sensor handles negative computation results."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    # Set up measures where result would be negative: 100 - 300 - 200 = -400
    total_measures = _create_mock_total_measures(produced_energy=100.0, green_energy=300.0, msb_charge=200.0)

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device], states=[], total_measures=total_measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == -400.0  # Should allow negative values


def test_grid_returned_energy_sensor__should_round_result_to_two_decimal_places():
    """Test that sensor rounds the result to 2 decimal places."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    # Set up measures that would produce a precise decimal result
    total_measures = _create_mock_total_measures(
        produced_energy=123.456789, green_energy=12.123456, msb_charge=5.987654
    )

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device], states=[], total_measures=total_measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    # 123.456789 - 12.123456 - 5.987654 = 105.345679
    assert result == 105.35  # Should be rounded to 2 decimal places


def test_grid_returned_energy_sensor__should_convert_ws_to_wh():
    """Test that sensor converts Ws (watt-seconds) to Wh (watt-hours) when needed."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    # Set up measures in Ws units: 3600 Ws = 1 Wh
    total_measures = _create_mock_total_measures(
        produced_energy=7200.0,  # 7200 Ws = 2 Wh
        green_energy=3600.0,  # 3600 Ws = 1 Wh
        msb_charge=1800.0,  # 1800 Ws = 0.5 Wh
        unit="Ws",
    )

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device], states=[], total_measures=total_measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 0.5  # 2 - 1 - 0.5 = 0.5 Wh


def test_grid_returned_energy_sensor__should_generate_correct_unique_id():
    """Test that sensor generates unique_id with subscription_id pattern."""
    # Given
    subscription_id = "SUB12345"
    virtual_device_id = "virtual-device-001"

    mock_coordinator = _create_mock_coordinator(subscription_id)
    virtual_device = _create_mock_virtual_device(virtual_device_id)

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[virtual_device], states=[], total_measures=[])

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]

    # When
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device_id,
        description=description,
    )

    # Then
    expected_unique_id = "sub12345_virtual_device_001_grid_returned_energy"
    assert sensor.unique_id == expected_unique_id


def test_grid_returned_energy_sensor__should_have_correct_extra_attributes():
    """Test that sensor has correct extra state attributes showing the computation."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    total_measures = _create_mock_total_measures(produced_energy=1000.0, green_energy=300.0, msb_charge=200.0)

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device], states=[], total_measures=total_measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    attributes = sensor.extra_state_attributes

    # Then
    expected_attributes = {
        "data_source": "computed_from_total_measures",
    }
    assert attributes == expected_attributes


def test_grid_returned_energy_sensor__should_be_available_when_coordinator_successful():
    """Test that sensor is available when coordinator update is successful and device exists."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[virtual_device], states=[], total_measures=[])

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    is_available = sensor.available

    # Then
    assert is_available is True


def test_grid_returned_energy_sensor__should_not_be_available_when_coordinator_failed():
    """Test that sensor is not available when coordinator update failed."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_coordinator.last_update_success = False  # Coordinator update failed
    virtual_device = _create_mock_virtual_device()

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[virtual_device], states=[], total_measures=[])

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    is_available = sensor.available

    # Then
    assert is_available is False


def test_grid_returned_energy_sensor__should_handle_none_coordinator_data():
    """Test that sensor returns 0 when coordinator data is None."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_coordinator.data = None
    virtual_device = _create_mock_virtual_device()

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 0.0  # Should return 0 when no data available


def test_grid_returned_energy_sensor__should_handle_none_total_measures():
    """Test that sensor returns 0 when total_measures is None."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    virtual_device = _create_mock_virtual_device()

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[virtual_device],
        states=[],
        total_measures=None,  # No total measures
    )

    description = SENSOR_TYPE_MAPPING["grid_returned_energy"]
    sensor = MyLightSystemsGridReturnedEnergySensor(
        coordinator=mock_coordinator,
        virtual_device_id=virtual_device.id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result == 0.0  # Should return 0 when no total measures
