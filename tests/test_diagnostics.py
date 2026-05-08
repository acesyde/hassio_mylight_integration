"""Unit tests for diagnostics."""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mylight_systems.api.const import PROFILE_URL
from custom_components.mylight_systems.api.exceptions import CommunicationError
from custom_components.mylight_systems.diagnostics import (
    DIAGNOSTIC_ENDPOINTS,
    _anonymize_response,
    async_get_config_entry_diagnostics,
)

# ---------------------------------------------------------------------------
# _anonymize_response tests
# ---------------------------------------------------------------------------


class TestAnonymizeResponse:
    """Tests for the _anonymize_response function."""

    def test_removes_auth_token(self):
        data = {"status": "ok", "authToken": "secret123"}
        result = _anonymize_response(data)
        assert "authToken" not in result
        assert result["status"] == "ok"

    def test_redacts_pii_fields(self):
        data = {
            "email": "user@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "tenant": "myhome",
        }
        result = _anonymize_response(data)
        assert result["email"] == "***"
        assert result["firstName"] == "***"
        assert result["lastName"] == "***"
        assert result["tenant"] == "***"

    def test_zeroes_location_fields(self):
        data = {"latitude": "48.8566", "longitude": "2.3522"}
        result = _anonymize_response(data)
        assert result["latitude"] == 0.0
        assert result["longitude"] == 0.0

    def test_truncates_id_fields(self):
        data = {
            "id": "40oXYqq6nM7R9zGK",
            "deviceId": "bat-001-abcdef",
            "sensorId": "bat-001-soc-xyz",
            "serialNumber": "SN12345678",
        }
        result = _anonymize_response(data)
        assert result["id"] == "40oX***"
        assert result["deviceId"] == "bat-***"
        assert result["sensorId"] == "bat-***"
        assert result["serialNumber"] == "SN12***"

    def test_keeps_short_ids_unchanged(self):
        data = {"id": "abcd"}
        result = _anonymize_response(data)
        assert result["id"] == "abcd"

    def test_recurses_into_nested_dicts(self):
        data = {
            "status": "ok",
            "deviceStates": [
                {
                    "deviceId": "bat-001-abcdef",
                    "sensorStates": [{"sensorId": "bat-001-soc-xyz", "measure": {"type": "soc", "value": 75}}],
                }
            ],
        }
        result = _anonymize_response(data)
        assert result["deviceStates"][0]["deviceId"] == "bat-***"
        assert result["deviceStates"][0]["sensorStates"][0]["sensorId"] == "bat-***"
        assert result["deviceStates"][0]["sensorStates"][0]["measure"]["type"] == "soc"

    def test_preserves_non_sensitive_fields(self):
        data = {"status": "ok", "gridType": "1 phase", "name": "Habitation"}
        result = _anonymize_response(data)
        assert result == data

    def test_handles_profile_response(self):
        data = {
            "status": "ok",
            "tenant": "myhome",
            "id": "40oXYqq6nM7R9zGK",
            "email": "marc.dupond@fakedomain.com",
            "firstName": "Marc",
            "lastName": "Dupond",
            "latitude": "10.65797726931048",
            "longitude": "-0.1246704361536673",
            "subscription_status": "ok",
            "gridType": "1 phase",
        }
        result = _anonymize_response(data)
        assert result["email"] == "***"
        assert result["firstName"] == "***"
        assert result["lastName"] == "***"
        assert result["tenant"] == "***"
        assert result["latitude"] == 0.0
        assert result["longitude"] == 0.0
        assert result["id"] == "40oX***"
        assert result["status"] == "ok"
        assert result["gridType"] == "1 phase"


# ---------------------------------------------------------------------------
# async_get_config_entry_diagnostics tests
# ---------------------------------------------------------------------------


def _make_mock_entry(entry_data: dict) -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = entry_data
    return entry


def _make_mock_coordinator(auth_token: str = "test-token", data=None) -> MagicMock:  # noqa: S107
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.auth_token = auth_token
    coordinator.authenticate_user = AsyncMock()
    coordinator.data = data
    return coordinator


ENTRY_DATA = {
    "email": "test@example.com",
    "password": "secret",
    "grid_type": "one_phase",
    "virtual_device_id": "vrt-123456",
    "subscription_id": "sub-123",
    "master_id": "mst-123",
    "relay_devices": [
        {"id": "sw-123-water", "name": "Relais", "device_type_id": "water_heater", "type_override": "MST-G3-Relay"},
    ],
    "gmd_devices": [
        {
            "id": "gmd-composite-1",
            "name": "Compteur",
            "device_type_id": None,
            "type_override": None,
            "is_composite": True,
        },
    ],
}


@pytest.mark.asyncio
async def test_diagnostics_returns_all_endpoint_keys():
    """Test that raw_api_responses contains all expected endpoint keys."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.async_raw_request = AsyncMock(return_value={"status": "ok"})

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    static_labels = {label for label, *_ in DIAGNOSTIC_ENDPOINTS}
    keys = set(result["raw_api_responses"].keys())

    # All static endpoints are present
    assert static_labels.issubset(keys)
    # ENTRY_DATA declares one composite gmd → one extra per-gmd grouping label
    extra = keys - static_labels
    assert len(extra) == 1
    assert next(iter(extra)).startswith("measures_grouping__gmd_0_")


@pytest.mark.asyncio
async def test_diagnostics_base64_decodes_to_valid_json():
    """Test that each raw_api_responses value is valid base64 JSON."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.async_raw_request = AsyncMock(return_value={"status": "ok", "data": [1, 2, 3]})

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    for path, encoded in result["raw_api_responses"].items():
        decoded = json.loads(base64.b64decode(encoded))
        assert isinstance(decoded, dict), f"Decoded response for {path} is not a dict"
        assert decoded["status"] == "ok"


@pytest.mark.asyncio
async def test_diagnostics_anonymizes_auth_token():
    """Test that authToken is stripped from raw responses."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.async_raw_request = AsyncMock(
        return_value={"status": "ok", "authToken": "should-be-removed"}
    )

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    for encoded in result["raw_api_responses"].values():
        decoded = json.loads(base64.b64decode(encoded))
        assert "authToken" not in decoded


@pytest.mark.asyncio
async def test_diagnostics_captures_endpoint_errors():
    """Test that a failing endpoint produces an error entry instead of crashing."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()

    call_count = 0

    async def _mock_raw_request(method, path, params=None):
        nonlocal call_count
        call_count += 1
        if path == PROFILE_URL:
            raise CommunicationError()
        return {"status": "ok"}

    mock_coordinator.client.async_raw_request = _mock_raw_request

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    # All static endpoints should still be present (per-gmd ones may also exist)
    static_labels = {label for label, *_ in DIAGNOSTIC_ENDPOINTS}
    assert static_labels.issubset(set(result["raw_api_responses"].keys()))

    # The failed endpoint should have an error payload
    profile_decoded = json.loads(base64.b64decode(result["raw_api_responses"]["profile"]))
    assert "error" in profile_decoded
    assert profile_decoded["error"] == "CommunicationError"

    # Other endpoints should have normal responses
    devices_decoded = json.loads(base64.b64decode(result["raw_api_responses"]["devices"]))
    assert devices_decoded["status"] == "ok"


@pytest.mark.asyncio
async def test_diagnostics_returns_empty_responses_on_auth_failure():
    """Test that diagnostics still returns when authentication fails."""
    mock_coordinator = MagicMock()
    mock_coordinator.authenticate_user = AsyncMock(side_effect=Exception("auth failed"))
    mock_coordinator.data = None

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["raw_api_responses"] == {}
    assert result["coordinator_data"] is None
    assert "integration_manifest" in result


@pytest.mark.asyncio
async def test_diagnostics_per_gmd_labels_with_two_gmds():
    """When the entry declares multiple gmds, raw_api_responses contains one labelled call per gmd."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.async_raw_request = AsyncMock(return_value={"status": "ok"})

    entry_data_with_two_gmds = {
        **ENTRY_DATA,
        "gmd_devices": [
            {"id": "gmd-comp", "name": "Compteur", "device_type_id": None, "type_override": None, "is_composite": True},
            {
                "id": "gmd-wh",
                "name": "Compteur 1",
                "device_type_id": "water_heater",
                "type_override": "MC1D01RM",
                "is_composite": False,
            },
        ],
    }
    entry = _make_mock_entry(entry_data_with_two_gmds)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    keys = set(result["raw_api_responses"].keys())
    per_gmd_keys = {k for k in keys if k.startswith("measures_grouping__gmd_")}
    assert per_gmd_keys == {
        "measures_grouping__gmd_0_generic_composite",
        "measures_grouping__gmd_1_water_heater_submeter",
    }


@pytest.mark.asyncio
async def test_diagnostics_redacts_id_inside_relay_and_gmd_lists():
    """The `id` field inside relay_devices and gmd_devices should be truncated."""
    mock_coordinator = _make_mock_coordinator()
    mock_coordinator.client = MagicMock()
    mock_coordinator.client.async_raw_request = AsyncMock(return_value={"status": "ok"})

    entry = _make_mock_entry(ENTRY_DATA)
    entry.runtime_data = mock_coordinator

    hass = MagicMock()
    mock_integration = MagicMock()
    mock_integration.domain = "mylight_systems"
    mock_integration.version = "1.0.0"

    with patch(
        "custom_components.mylight_systems.diagnostics.async_get_integration",
        return_value=mock_integration,
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)

    relay_id = result["config_entry_data"]["relay_devices"][0]["id"]
    gmd_id = result["config_entry_data"]["gmd_devices"][0]["id"]
    assert relay_id == "sw-1***"  # "sw-123-water" → first 4 chars + ***
    assert gmd_id == "gmd-***"
