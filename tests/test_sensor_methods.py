"""Tests for internal methods in mylight_systems sensor."""

from unittest.mock import Mock

from custom_components.mylight_systems.const import CONF_SUBSCRIPTION_ID
from custom_components.mylight_systems.coordinator import MyLightSystemsCoordinatorData
from custom_components.mylight_systems.sensor import (
    SENSOR_TYPE_MAPPING,
    TOTAL_MEASURES_MAPPING,
    MyLightSystemsSensor,
)


def _create_mock_coordinator(subscription_id: str = "test123"):
    """Create a mock coordinator for testing."""
    mock_coordinator = Mock()
    mock_coordinator.config_entry = Mock()
    mock_coordinator.config_entry.data = {CONF_SUBSCRIPTION_ID: subscription_id}
    mock_coordinator.last_update_success = True
    return mock_coordinator


class TestGetTotalMeasureValue:
    """Test cases for _get_total_measure_value method."""

    def test_get_total_measure_value__should_return_none_when_no_coordinator_data(self):
        """Test that method returns None when coordinator has no data."""
        # Given
        mock_coordinator = _create_mock_coordinator()

        # Create minimal valid data for sensor construction
        mock_device = Mock()
        mock_device.id = "test-device"
        mock_device.name = "Test Device"
        mock_device.device_type_name = "Test Type"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "test-sensor"

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["produced_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # Now set coordinator data to None to test the method
        mock_coordinator.data = None

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert result is None

    def test_get_total_measure_value__should_return_none_when_no_total_measures(self):
        """Test that method returns None when coordinator data has no total_measures."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[], total_measures=None)

        description = SENSOR_TYPE_MAPPING["produced_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert result is None

    def test_get_total_measure_value__should_return_none_when_empty_total_measures(self):
        """Test that method returns None when total_measures is empty dict."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[], total_measures={})

        description = SENSOR_TYPE_MAPPING["produced_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert result is None

    def test_get_total_measure_value__should_return_none_when_sensor_key_not_in_mapping(self):
        """Test that method returns None when sensor key has no total_measures mapping."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_measure = Mock()
        mock_measure.type = "some_measure"
        mock_total_measures = [mock_measure]
        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        # Use a sensor type that's not in TOTAL_MEASURES_MAPPING
        description = SENSOR_TYPE_MAPPING["electric_power"]  # This key is not in TOTAL_MEASURES_MAPPING
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert result is None

    def test_get_total_measure_value__should_return_none_when_measure_type_not_in_total_measures(self):
        """Test that method returns None when measure type is not in total_measures dict."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_measure = Mock()
        mock_measure.type = "other_measure"  # Different from what we're looking for
        mock_total_measures = [mock_measure]
        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        description = SENSOR_TYPE_MAPPING["produced_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert result is None

    def test_get_total_measure_value__should_return_measure_value_when_measure_has_value_attribute(self):
        """Test that method returns measure.value when measure has value attribute."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_measure = Mock()
        mock_measure.type = "produced_energy"
        mock_measure.value = 123.45

        mock_total_measures = [mock_measure]
        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        description = SENSOR_TYPE_MAPPING["produced_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert 123.45 == result

    def test_get_total_measure_value__should_return_measure_directly_when_no_value_attribute(self):
        """Test that method returns measure directly when measure has no value attribute."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        # Create a measure without value attribute (e.g., just a number)
        mock_measure = Mock(spec=["type"])  # Only allow 'type' attribute
        mock_measure.type = "grid_energy"
        # Don't set .value attribute to test the fallback

        mock_total_measures = [mock_measure]
        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        description = SENSOR_TYPE_MAPPING["grid_energy"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert mock_measure == result

    def test_get_total_measure_value__should_work_with_all_mapped_sensor_types(self):
        """Test that method works correctly with all sensor types in TOTAL_MEASURES_MAPPING."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        # Create measures for all mapped types
        mock_total_measures = []
        expected_values = {}

        for sensor_key, total_measure_type in TOTAL_MEASURES_MAPPING.items():
            mock_measure = Mock()
            mock_measure.type = total_measure_type
            mock_measure.value = float(hash(sensor_key) % 1000)  # Generate unique test values
            mock_total_measures.append(mock_measure)
            expected_values[sensor_key] = mock_measure.value

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        # Test each mapped sensor type
        for sensor_key in TOTAL_MEASURES_MAPPING.keys():
            if sensor_key in SENSOR_TYPE_MAPPING:
                description = SENSOR_TYPE_MAPPING[sensor_key]
                sensor = MyLightSystemsSensor(
                    coordinator=mock_coordinator,
                    device_id="test-device",
                    sensor_id="test-sensor",
                    description=description,
                )

                # When
                result = sensor._get_total_measure_value()

                # Then
                assert expected_values[sensor_key] == result

    def test_get_total_measure_value__should_return_integer_value_when_measure_is_integer(self):
        """Test that method returns integer value when measure value is integer."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_measure = Mock()
        mock_measure.type = "autonomy_rate"
        mock_measure.value = 100  # Integer value

        mock_total_measures = [mock_measure]
        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[], total_measures=mock_total_measures
        )

        description = SENSOR_TYPE_MAPPING["autonomy_rate"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_total_measure_value()

        # Then
        assert 100 == result
        assert isinstance(result, int)


class TestGetCurrentSensorState:
    """Test cases for _get_current_sensor_state method."""

    def test_get_current_sensor_state__should_return_none_when_no_coordinator_data(self):
        """Test that method returns None when coordinator has no data."""
        # Given
        mock_coordinator = _create_mock_coordinator()

        # Create minimal valid data for sensor construction
        mock_device = Mock()
        mock_device.id = "test-device"
        mock_device.name = "Test Device"
        mock_device.device_type_name = "Test Type"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "test-sensor"

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # Now set coordinator data to None to test the method
        mock_coordinator.data = None

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None

    def test_get_current_sensor_state__should_return_none_when_no_states(self):
        """Test that method returns None when coordinator data has no states."""
        # Given
        mock_coordinator = _create_mock_coordinator()

        # Create minimal valid data for sensor construction
        mock_device = Mock()
        mock_device.id = "test-device"
        mock_device.name = "Test Device"
        mock_device.device_type_name = "Test Type"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "test-sensor"

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # Now set states to None to test the method
        mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=None, total_measures={})

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None

    def test_get_current_sensor_state__should_return_none_when_empty_states(self):
        """Test that method returns None when states list is empty."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_coordinator.data = MyLightSystemsCoordinatorData(devices=[mock_device], states=[], total_measures={})

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None

    def test_get_current_sensor_state__should_return_none_when_device_not_found(self):
        """Test that method returns None when device_id is not found in states."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        # Create a state for a different device
        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "test-sensor"

        mock_device_state = Mock()
        mock_device_state.device_id = "different-device"  # Different device ID
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",  # Looking for this device
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None

    def test_get_current_sensor_state__should_return_none_when_sensor_not_found(self):
        """Test that method returns None when sensor_id is not found in device states."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        # Create a sensor state for a different sensor
        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "different-sensor"  # Different sensor ID

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",  # Looking for this sensor
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None

    def test_get_current_sensor_state__should_return_sensor_state_when_found(self):
        """Test that method returns correct sensor state when device and sensor are found."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "test-sensor"
        mock_sensor_state.measure = Mock()
        mock_sensor_state.measure.value = 100.0

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert mock_sensor_state == result

    def test_get_current_sensor_state__should_return_correct_sensor_from_multiple_sensors(self):
        """Test that method returns correct sensor state when multiple sensors exist."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        # Create multiple sensor states
        mock_sensor_state_1 = Mock()
        mock_sensor_state_1.sensor_id = "sensor-1"
        mock_sensor_state_1.measure = Mock()
        mock_sensor_state_1.measure.value = 100.0

        mock_sensor_state_2 = Mock()
        mock_sensor_state_2.sensor_id = "sensor-2"
        mock_sensor_state_2.measure = Mock()
        mock_sensor_state_2.measure.value = 200.0

        mock_sensor_state_3 = Mock()
        mock_sensor_state_3.sensor_id = "test-sensor"  # This is the one we want
        mock_sensor_state_3.measure = Mock()
        mock_sensor_state_3.measure.value = 300.0

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state_1, mock_sensor_state_2, mock_sensor_state_3]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert mock_sensor_state_3 == result
        assert 300.0 == result.measure.value

    def test_get_current_sensor_state__should_return_correct_device_from_multiple_devices(self):
        """Test that method returns sensor state from correct device when multiple devices exist."""
        # Given
        mock_coordinator = _create_mock_coordinator()

        # Create multiple devices
        mock_device_1 = Mock()
        mock_device_1.id = "device-1"

        mock_device_2 = Mock()
        mock_device_2.id = "test-device"  # This is the one we want

        # Create sensor states for different devices
        mock_sensor_state_1 = Mock()
        mock_sensor_state_1.sensor_id = "test-sensor"
        mock_sensor_state_1.measure = Mock()
        mock_sensor_state_1.measure.value = 100.0

        mock_sensor_state_2 = Mock()
        mock_sensor_state_2.sensor_id = "test-sensor"  # Same sensor ID but different device
        mock_sensor_state_2.measure = Mock()
        mock_sensor_state_2.measure.value = 200.0

        mock_device_state_1 = Mock()
        mock_device_state_1.device_id = "device-1"
        mock_device_state_1.sensor_states = [mock_sensor_state_1]

        mock_device_state_2 = Mock()
        mock_device_state_2.device_id = "test-device"
        mock_device_state_2.sensor_states = [mock_sensor_state_2]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device_1, mock_device_2], states=[mock_device_state_1, mock_device_state_2], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert mock_sensor_state_2 == result
        assert 200.0 == result.measure.value

    def test_get_current_sensor_state__should_handle_case_sensitive_ids(self):
        """Test that method handles case-sensitive device and sensor IDs correctly."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "Test-Sensor"  # Mixed case
        mock_sensor_state.measure = Mock()
        mock_sensor_state.measure.value = 100.0

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="Test-Sensor",  # Exact case match required
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert mock_sensor_state == result

    def test_get_current_sensor_state__should_return_none_when_case_mismatch(self):
        """Test that method returns None when device or sensor ID case doesn't match."""
        # Given
        mock_coordinator = _create_mock_coordinator()
        mock_device = Mock()
        mock_device.id = "test-device"

        mock_sensor_state = Mock()
        mock_sensor_state.sensor_id = "Test-Sensor"  # Mixed case
        mock_sensor_state.measure = Mock()
        mock_sensor_state.measure.value = 100.0

        mock_device_state = Mock()
        mock_device_state.device_id = "test-device"
        mock_device_state.sensor_states = [mock_sensor_state]

        mock_coordinator.data = MyLightSystemsCoordinatorData(
            devices=[mock_device], states=[mock_device_state], total_measures={}
        )

        description = SENSOR_TYPE_MAPPING["electric_power"]
        sensor = MyLightSystemsSensor(
            coordinator=mock_coordinator,
            device_id="test-device",
            sensor_id="test-sensor",  # Different case - should not match
            description=description,
        )

        # When
        result = sensor._get_current_sensor_state()

        # Then
        assert result is None
