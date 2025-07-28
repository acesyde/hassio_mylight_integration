"""Test sensor entity creation from device states."""

from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower

from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import (
    SENSOR_TYPE_MAPPING,
    MyLightSystemsSensor,
)


def test_sensor_type_mapping__should_have_correct_power_sensor_config():
    """Test that electric_power sensor type has correct configuration."""
    # Given
    expected_config = {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "Power",
    }

    # When
    actual_config = SENSOR_TYPE_MAPPING["electric_power"]

    # Then
    assert expected_config == actual_config


def test_sensor_type_mapping__should_have_correct_energy_sensor_config():
    """Test that produced_energy sensor type has correct configuration."""
    # Given
    expected_config = {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.WATT_HOUR,
        "state_class": SensorStateClass.TOTAL,
        "name_suffix": "Produced Energy",
    }

    # When
    actual_config = SENSOR_TYPE_MAPPING["produced_energy"]

    # Then
    assert expected_config == actual_config


def test_sensor_type_mapping__should_have_correct_percentage_sensor_config():
    """Test that autonomy_rate sensor type has correct configuration."""
    # Given
    expected_config = {
        "device_class": None,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name_suffix": "Autonomy Rate",
    }

    # When
    actual_config = SENSOR_TYPE_MAPPING["autonomy_rate"]

    # Then
    assert expected_config == actual_config


def test_mylight_systems_sensor__should_convert_ws_to_wh_for_energy():
    """Test that Ws values are converted to Wh for energy sensors."""
    # Given
    mock_coordinator = Mock()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = "test-sensor"
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "produced_energy"
    mock_sensor_state.measure.value = 3600.0  # 3600 Ws = 1 Wh
    mock_sensor_state.measure.unit = "Ws"
    mock_sensor_state.measure.date = "2025-07-28 13:50:00"

    mock_device_state = Mock()
    mock_device_state.device_id = "test-device"
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    sensor_config = SENSOR_TYPE_MAPPING["produced_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        sensor_config=sensor_config,
    )

    # When
    result = sensor.native_value

    # Then
    assert 1.0 == result  # 3600 Ws converted to 1.0 Wh


def test_mylight_systems_sensor__should_return_raw_value_for_power():
    """Test that power sensor returns raw watt values without conversion."""
    # Given
    mock_coordinator = Mock()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = "test-sensor"
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "electric_power"
    mock_sensor_state.measure.value = 2412.47
    mock_sensor_state.measure.unit = "watt"
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = "test-device"
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    sensor_config = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        sensor_config=sensor_config,
    )

    # When
    result = sensor.native_value

    # Then
    assert 2412.47 == result


def test_mylight_systems_sensor__should_return_none_when_no_sensor_state():
    """Test that sensor returns None when sensor state is not found."""
    # Given
    mock_coordinator = Mock()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"

    mock_coordinator.data = MyLightSystemsCoordinatorData(
        devices=[mock_device],
        states=[],  # No states
    )

    sensor_config = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="non-existent-sensor",
        sensor_config=sensor_config,
    )

    # When
    result = sensor.native_value

    # Then
    assert None == result


def test_mylight_systems_sensor__should_have_correct_extra_attributes():
    """Test that sensor has correct extra state attributes."""
    # Given
    mock_coordinator = Mock()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = "test-sensor"
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "electric_power"
    mock_sensor_state.measure.value = 2412.47
    mock_sensor_state.measure.unit = "watt"
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = "test-device"
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    sensor_config = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        sensor_config=sensor_config,
    )

    # When
    result = sensor.extra_state_attributes

    # Then
    expected_attributes = {
        "sensor_id": "test-sensor",
        "measure_type": "electric_power",
        "original_unit": "watt",
        "last_updated": "2025-07-28 13:54:42",
    }
    assert expected_attributes == result
