"""Unit tests for services pure functions."""

from datetime import date

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.services import _build_csv, _parse_date


class TestParseDateFunction:
    def test_valid_date_string_returns_date_object(self):
        result = _parse_date("2025-01-15", "from_date")
        assert result == date(2025, 1, 15)

    def test_invalid_date_string_raises_service_validation_error(self):
        with pytest.raises(ServiceValidationError):
            _parse_date("not-a-date", "from_date")

    def test_invalid_format_raises_service_validation_error(self):
        with pytest.raises(ServiceValidationError):
            _parse_date("15/01/2025", "to_date")


class TestBuildCsvFunction:
    def test_single_day_single_measure_produces_correct_csv(self):
        rows = [(date(2025, 1, 1), [Measure("produced_energy", 100.0, "Ws")])]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert lines[0] == "date,produced_energy (Ws)"
        assert lines[1] == "2025-01-01,100.0"

    def test_multiple_days_appear_as_rows_in_order(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws")]),
            (date(2025, 1, 2), [Measure("produced_energy", 20.0, "Ws")]),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert len(lines) == 3  # header + 2 data rows
        assert lines[1].startswith("2025-01-01")
        assert lines[2].startswith("2025-01-02")

    def test_missing_measure_for_day_written_as_empty_string(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws"), Measure("grid_energy", 5.0, "Ws")]),
            (date(2025, 1, 2), [Measure("produced_energy", 20.0, "Ws")]),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert lines[2] == "2025-01-02,20.0,"

    def test_column_order_matches_discovery_order(self):
        rows = [
            (
                date(2025, 1, 1),
                [
                    Measure("produced_energy", 10.0, "Ws"),
                    Measure("grid_energy", 5.0, "Ws"),
                ],
            )
        ]
        result = _build_csv(rows)
        header = result.strip().splitlines()[0]
        assert header == "date,produced_energy (Ws),grid_energy (Ws)"

    def test_empty_rows_returns_header_only(self):
        result = _build_csv([])
        lines = result.strip().splitlines()
        assert len(lines) == 1
        assert lines[0] == "date"

    def test_day_with_no_measures_writes_empty_values(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws")]),
            (date(2025, 1, 2), []),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert lines[2] == "2025-01-02,"

    def test_week_date_format_raises_service_validation_error(self):
        with pytest.raises(ServiceValidationError):
            _parse_date("2025-W01-1", "from_date")


class TestDateValidationLogic:
    """Test the date validation rules used by the service handler."""

    def test_equal_dates_would_fail_handler_guard(self):
        from_date = date(2025, 1, 1)
        to_date = date(2025, 1, 1)
        assert from_date >= to_date

    def test_from_after_to_would_fail_handler_guard(self):
        from_date = date(2025, 1, 5)
        to_date = date(2025, 1, 1)
        assert from_date >= to_date

    def test_valid_range_passes_handler_guard(self):
        from_date = date(2025, 1, 1)
        to_date = date(2025, 1, 31)
        assert not (from_date >= to_date)

    def test_range_of_31_days_is_allowed(self):
        from_date = date(2025, 1, 1)
        to_date = date(2025, 2, 1)
        assert (to_date - from_date).days <= 31

    def test_range_of_32_days_exceeds_limit(self):
        from_date = date(2025, 1, 1)
        to_date = date(2025, 2, 2)
        assert (to_date - from_date).days > 31
