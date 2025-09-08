"""Tests for native_value method in mylight_systems sensor."""

from unittest.mock import Mock

from custom_components.mylight_systems.const import CONF_SUBSCRIPTION_ID
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import (
    SENSOR_TYPE_MAPPING,
    MyLightSystemsSensor,
)


def _create_mock_coordinator(subscription_id: str = "test123"):
    """Create a mock coordinator for testing."""
    mock_coordinator = Mock()
    mock_coordinator.config_entry = Mock()
    mock_coordinator.config_entry.data = {CONF_SUBSCRIPTION_ID: subscription_id}
    mock_coordinator.last_update_success = True
    return mock_coordinator


def _create_mock_sensor_setup(
    coordinator, device_id: str, sensor_id: str, measure_type: str, value: float, unit: str = "watt"
):
    """Create mock sensor setup with device and sensor state."""
    mock_device = Mock()
    mock_device.id = device_id
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = sensor_id
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = measure_type
    mock_sensor_state.measure.value = value
    mock_sensor_state.measure.unit = unit
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = device_id
    mock_device_state.sensor_states = [mock_sensor_state]

    coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    return mock_device, mock_sensor_state, mock_device_state


def test_native_value__should_return_positive_value_when_grid_energy_is_negative():
    """Test that grid_energy sensor returns positive value when original value is negative."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    negative_value = -150.75

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", negative_value, "Wh")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 150.75 == result  # Should be positive (absolute value)


def test_native_value__should_return_positive_value_when_grid_energy_is_already_positive():
    """Test that grid_energy sensor returns same positive value when original value is positive."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    positive_value = 250.50

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", positive_value, "Wh")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 250.50 == result  # Should remain positive


def test_native_value__should_return_zero_when_grid_energy_is_zero():
    """Test that grid_energy sensor returns zero when original value is zero."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    zero_value = 0.0

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", zero_value, "Wh")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 0.0 == result  # Should remain zero


def test_native_value__should_not_affect_other_sensor_types_when_negative():
    """Test that non-grid_energy sensors can return negative values unchanged."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    negative_value = -100.25

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "electric_power", negative_value, "watt")

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert -100.25 == result  # Should remain negative for non-grid_energy sensors


def test_native_value__should_convert_ws_to_wh_and_apply_positive_rule_for_grid_energy():
    """Test that grid_energy sensor converts Ws to Wh and ensures positive value."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    negative_ws_value = -7200.0  # -7200 Ws = -2 Wh

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", negative_ws_value, "Ws")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 2.0 == result  # Should convert -7200 Ws to positive 2.0 Wh


def test_native_value__should_convert_ws_to_wh_for_produced_energy():
    """Test that produced_energy sensor converts Ws to Wh correctly."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    ws_value = 10800.0  # 10800 Ws = 3 Wh

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "produced_energy", ws_value, "Ws")

    description = SENSOR_TYPE_MAPPING["produced_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 3.0 == result  # Should convert 10800 Ws to 3.0 Wh


def test_native_value__should_round_float_values_to_two_decimal_places():
    """Test that float values are rounded to 2 decimal places."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    precise_value = 123.456789

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "electric_power", precise_value, "watt")

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 123.46 == result  # Should be rounded to 2 decimal places


def test_native_value__should_round_ws_to_wh_conversion_to_two_decimal_places():
    """Test that Ws to Wh conversion results are rounded to 2 decimal places."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    ws_value = 3661.0  # 3661 Ws = 1.0169444... Wh

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "produced_energy", ws_value, "Ws")

    description = SENSOR_TYPE_MAPPING["produced_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 1.02 == result  # Should be rounded to 2 decimal places


def test_native_value__should_return_integer_values_unchanged():
    """Test that integer values are returned without modification."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    integer_value = 150

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "electric_power", integer_value, "watt")

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 150 == result  # Should remain as integer


def test_native_value__should_return_none_when_no_sensor_state():
    """Test that sensor returns None when sensor state is not found."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[mock_device],
        states=[],  # No states
    )

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="non-existent-sensor",
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result is None


def test_native_value__should_return_none_when_no_measure():
    """Test that sensor returns None when measure is None."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"

    mock_device = Mock()
    mock_device.id = device_id
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = sensor_id
    mock_sensor_state.measure = None  # No measure

    mock_device_state = Mock()
    mock_device_state.device_id = device_id
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert result is None


def test_native_value__should_handle_grid_energy_with_negative_integer():
    """Test that grid_energy sensor handles negative integer values correctly."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    negative_integer = -42

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", negative_integer, "Wh")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    assert 42 == result  # Should be positive integer


def test_native_value__should_handle_complex_grid_energy_ws_conversion_with_negative():
    """Test grid_energy sensor with complex Ws to Wh conversion and negative value handling."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    device_id = "test-device"
    sensor_id = "test-sensor"
    negative_ws_value = -5432.1  # Complex negative Ws value

    _create_mock_sensor_setup(mock_coordinator, device_id, sensor_id, "grid_energy", negative_ws_value, "Ws")

    description = SENSOR_TYPE_MAPPING["grid_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # When
    result = sensor.native_value

    # Then
    # -5432.1 Ws / 3600 = -1.5089166... Wh -> abs() -> 1.51 Wh (rounded)
    assert 1.51 == result
