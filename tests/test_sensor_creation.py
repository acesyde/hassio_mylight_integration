"""Tests for sensor creation in mylight_systems integration."""

from unittest.mock import Mock

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)

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


def test_sensor_type_mapping__should_have_correct_power_sensor_config():
    """Test that electric_power sensor type has correct configuration."""
    # When
    actual_description = SENSOR_TYPE_MAPPING["electric_power"]

    # Then
    assert actual_description.key == "electric_power"
    assert actual_description.device_class == SensorDeviceClass.POWER
    assert actual_description.native_unit_of_measurement == UnitOfPower.WATT
    assert actual_description.state_class == SensorStateClass.MEASUREMENT
    assert actual_description.name == "Power"


def test_sensor_type_mapping__should_have_correct_energy_sensor_config():
    """Test that produced_energy sensor type has correct configuration."""
    # When
    actual_description = SENSOR_TYPE_MAPPING["produced_energy"]

    # Then
    assert actual_description.key == "produced_energy"
    assert actual_description.device_class == SensorDeviceClass.ENERGY
    assert actual_description.native_unit_of_measurement == UnitOfEnergy.WATT_HOUR
    assert actual_description.state_class == SensorStateClass.MEASUREMENT
    assert actual_description.name == "Produced Energy"


def test_sensor_type_mapping__should_have_correct_percentage_sensor_config():
    """Test that autonomy_rate sensor type has correct configuration."""
    # When
    actual_description = SENSOR_TYPE_MAPPING["autonomy_rate"]

    # Then
    assert actual_description.key == "autonomy_rate"
    assert actual_description.device_class is None
    assert actual_description.native_unit_of_measurement == PERCENTAGE
    assert actual_description.state_class == SensorStateClass.TOTAL
    assert actual_description.name == "Autonomy Rate"


def test_mylight_systems_sensor__should_convert_ws_to_wh_for_energy():
    """Test that Ws values are converted to Wh for energy sensors."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

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

    description = SENSOR_TYPE_MAPPING["produced_energy"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        description=description,
    )

    # When
    value = sensor.native_value

    # Then
    assert value == 1.0  # 3600 Ws converted to 1 Wh


def test_mylight_systems_sensor__should_return_raw_value_for_power():
    """Test that power sensor returns raw watt values without conversion."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

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

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        description=description,
    )

    # When
    value = sensor.native_value

    # Then
    assert value == 2412.47  # Raw value without conversion


def test_mylight_systems_sensor__should_return_none_when_no_sensor_state():
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

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="non-existent-sensor",
        description=description,
    )

    # When
    value = sensor.native_value

    # Then
    assert value is None


def test_mylight_systems_sensor__should_have_correct_extra_attributes():
    """Test that sensor has correct extra state attributes."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

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

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="test-sensor",
        description=description,
    )

    # When
    attributes = sensor.extra_state_attributes

    # Then
    expected_attributes = {
        "sensor_id": "test-sensor",
        "measure_type": "electric_power",
        "original_unit": "watt",
        "last_updated": "2025-07-28 13:54:42",
    }
    assert attributes == expected_attributes


def test_mylight_systems_sensor__should_have_lowercase_sensor_id_in_extra_attributes():
    """Test that sensor has lowercase sensor_id in extra state attributes."""
    # Given
    mock_coordinator = _create_mock_coordinator()
    mock_device = Mock()
    mock_device.id = "test-device"
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = "TEST-SENSOR-MIXED"  # Mixed case sensor ID
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "electric_power"
    mock_sensor_state.measure.value = 2412.47
    mock_sensor_state.measure.unit = "watt"
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = "test-device"
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    description = SENSOR_TYPE_MAPPING["electric_power"]
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id="test-device",
        sensor_id="TEST-SENSOR-MIXED",  # Pass mixed case ID
        description=description,
    )

    # When
    attributes = sensor.extra_state_attributes

    # Then
    assert attributes["sensor_id"] == "test-sensor-mixed"  # Should be lowercase


def test_mylight_systems_sensor__should_generate_correct_unique_id():
    """Test that sensor generates unique_id with subscription_id pattern."""
    # Given
    subscription_id = "SUB12345"
    device_id = "test-device-001"
    sensor_id = "test-sensor-001"

    mock_coordinator = _create_mock_coordinator(subscription_id)
    mock_device = Mock()
    mock_device.id = device_id
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = sensor_id
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "electric_power"
    mock_sensor_state.measure.value = 100.0
    mock_sensor_state.measure.unit = "watt"
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = device_id
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    description = SENSOR_TYPE_MAPPING["electric_power"]

    # When
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # Then
    expected_unique_id = "sub12345_test_device_001_test_sensor_001"
    assert sensor.unique_id == expected_unique_id


def test_mylight_systems_sensor__should_generate_lowercase_unique_id_with_mixed_case_input():
    """Test that sensor generates lowercase unique_id even with mixed case input."""
    # Given
    subscription_id = "SUB12345"  # Mixed case
    device_id = "TEST-DEVICE-001"  # Uppercase
    sensor_id = "Test-Sensor-001"  # Mixed case

    mock_coordinator = _create_mock_coordinator(subscription_id)
    mock_device = Mock()
    mock_device.id = device_id
    mock_device.name = "Test Device"
    mock_device.device_type_name = "Test Type"

    mock_sensor_state = Mock()
    mock_sensor_state.sensor_id = sensor_id
    mock_sensor_state.measure = Mock()
    mock_sensor_state.measure.type = "electric_power"
    mock_sensor_state.measure.value = 100.0
    mock_sensor_state.measure.unit = "watt"
    mock_sensor_state.measure.date = "2025-07-28 13:54:42"

    mock_device_state = Mock()
    mock_device_state.device_id = device_id
    mock_device_state.sensor_states = [mock_sensor_state]

    mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[mock_device_state])

    description = SENSOR_TYPE_MAPPING["electric_power"]

    # When
    sensor = MyLightSystemsSensor(
        coordinator=mock_coordinator,
        device_id=device_id,
        sensor_id=sensor_id,
        description=description,
    )

    # Then
    expected_unique_id = "sub12345_test_device_001_test_sensor_001"
    assert sensor.unique_id == expected_unique_id
