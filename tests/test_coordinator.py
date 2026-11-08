"""Unit tests for the coordinator."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.mylight_systems.api.exceptions import CommunicationError, UnauthorizedError
from custom_components.mylight_systems.api.models import InstallationDevices, Measure
from custom_components.mylight_systems.coordinator import MyLightSystemsDataUpdateCoordinator


@pytest.mark.asyncio
async def test_update_uses_home_assistant_local_date():
    """The measures window must follow HA's time zone, not the system date."""
    # 00:30 on 2 Jan in Paris is still 1 Jan in UTC.
    paris_now = datetime(2025, 1, 2, 0, 30, tzinfo=ZoneInfo("Europe/Paris"))
    config_entry = MagicMock()
    config_entry.options = {}
    config_entry.data = {
        "email": "user@example.com",
        "password": "secret",
        "grid_type": "grid",
        "virtual_device_id": "device",
        "virtual_battery_id": "battery",
    }
    client = MagicMock()
    client.async_get_measures_grouping = AsyncMock(return_value=[])
    client.async_get_measures_total = AsyncMock(return_value=[])
    client.async_get_battery_state = AsyncMock(return_value=None)
    client.async_get_devices = AsyncMock(return_value=InstallationDevices())
    coordinator = MyLightSystemsDataUpdateCoordinator(MagicMock(), client, config_entry)

    coordinator._MyLightSystemsDataUpdateCoordinator__auth_token = "token"  # noqa: S105

    with (
        patch.object(coordinator, "authenticate_user", AsyncMock()),
        patch("homeassistant.util.dt.now", return_value=paris_now),
    ):
        await coordinator._async_update_data()

    kwargs = client.async_get_measures_grouping.call_args.kwargs
    assert kwargs["from_date"] == "2025-01-02"
    assert kwargs["to_date"] == "2025-01-03"


def _build_coordinator(meter_id="meter-1", power=None, power_error=None):
    config_entry = MagicMock()
    config_entry.options = {}
    config_entry.data = {
        "email": "user@example.com",
        "password": "secret",
        "grid_type": "grid",
        "virtual_device_id": "device",
        "virtual_battery_id": "battery",
    }
    client = MagicMock()
    client.async_get_measures_grouping = AsyncMock(return_value=[])
    client.async_get_measures_total = AsyncMock(return_value=[])
    client.async_get_battery_state = AsyncMock(return_value=None)
    client.async_get_devices = AsyncMock(return_value=InstallationDevices(grid_meter_id=meter_id))
    client.async_get_grid_power = AsyncMock(return_value=power, side_effect=power_error)
    coordinator = MyLightSystemsDataUpdateCoordinator(MagicMock(), client, config_entry)
    coordinator._MyLightSystemsDataUpdateCoordinator__auth_token = "token"  # noqa: S105
    return coordinator, client


@pytest.mark.asyncio
async def test_update__should_expose_grid_power_and_discover_meter_once():
    """The meter is discovered on the first refresh only; power is read on every refresh."""
    power = Measure("electric_power", -1500.0, "watt")
    coordinator, client = _build_coordinator(power=power)

    with patch.object(coordinator, "authenticate_user", AsyncMock()):
        first = await coordinator._async_update_data()
        await coordinator._async_update_data()

    assert power == first.grid_power
    assert "meter-1" == coordinator.grid_meter_id
    assert 1 == client.async_get_devices.await_count
    assert 2 == client.async_get_grid_power.await_count


@pytest.mark.asyncio
async def test_update__should_not_read_grid_power_when_no_meter():
    """Without a single meter nothing is read and the id stays unset."""
    coordinator, client = _build_coordinator(meter_id=None)

    with patch.object(coordinator, "authenticate_user", AsyncMock()):
        data = await coordinator._async_update_data()

    assert coordinator.grid_meter_id is None
    assert data.grid_power is None
    client.async_get_grid_power.assert_not_awaited()


@pytest.mark.asyncio
async def test_update__should_keep_other_data_when_grid_power_read_fails():
    """A failing optional read must not fail the whole update."""
    coordinator, _ = _build_coordinator(power_error=CommunicationError())

    with patch.object(coordinator, "authenticate_user", AsyncMock()):
        data = await coordinator._async_update_data()

    assert data.grid_power is None


@pytest.mark.asyncio
async def test_update__should_keep_other_data_when_discovery_fails_and_retry_later():
    """A failing discovery is retried on the next refresh."""
    coordinator, client = _build_coordinator()
    client.async_get_devices.side_effect = [CommunicationError(), InstallationDevices(grid_meter_id="meter-1")]

    with patch.object(coordinator, "authenticate_user", AsyncMock()):
        await coordinator._async_update_data()
        assert coordinator.grid_meter_id is None
        await coordinator._async_update_data()

    assert "meter-1" == coordinator.grid_meter_id


@pytest.mark.asyncio
async def test_update__should_trigger_reauth_when_grid_power_unauthorized():
    """UnauthorizedError still propagates so reauth works."""
    coordinator, _ = _build_coordinator(power_error=UnauthorizedError())

    with (
        patch.object(coordinator, "authenticate_user", AsyncMock()),
        patch("custom_components.mylight_systems.coordinator.ir"),
        pytest.raises(ConfigEntryAuthFailed),
    ):
        await coordinator._async_update_data()


def _counters(discharge_ws, billed_ws):
    return [
        Measure("msb_discharge", discharge_ws, "watt_second"),
        Measure("grid_sans_msb_energy", billed_ws, "watt_second"),
    ]


async def _refresh_at(coordinator, client, minute, discharge_ws, billed_ws):
    client.async_get_measures_grouping.return_value = _counters(discharge_ws, billed_ws)
    at = datetime(2025, 1, 2, 18, minute, tzinfo=ZoneInfo("UTC"))
    with (
        patch.object(coordinator, "authenticate_user", AsyncMock()),
        patch("homeassistant.util.dt.utcnow", return_value=at),
    ):
        return await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_update__should_derive_virtual_battery_powers_from_counter_deltas():
    """Power is the counter delta over the elapsed time; unknown until two readings exist."""
    coordinator, client = _build_coordinator(meter_id=None)

    first = await _refresh_at(coordinator, client, 0, 1000.0, 5000.0)
    # 5 min later: +119 Wh discharged (1428 W), +0 billed.
    second = await _refresh_at(coordinator, client, 5, 1000.0 + 1428 * 300, 5000.0)

    assert (first.msb_discharge_power, first.grid_billed_power) == (None, None)
    assert second.msb_discharge_power == pytest.approx(1428)
    assert second.grid_billed_power == 0


@pytest.mark.asyncio
async def test_update__should_count_only_post_reset_energy_after_midnight():
    """A daily counter that went down restarted at midnight: only its new value counts."""
    coordinator, client = _build_coordinator(meter_id=None)

    await _refresh_at(coordinator, client, 0, 9_000_000.0, 9_000_000.0)
    data = await _refresh_at(coordinator, client, 5, 0.0, 600 * 300)

    assert data.msb_discharge_power == 0
    assert data.grid_billed_power == pytest.approx(600)


@pytest.mark.asyncio
async def test_update__should_not_derive_powers_without_virtual_battery():
    """Installations without a virtual battery never get these powers."""
    coordinator, client = _build_coordinator(meter_id=None)
    coordinator.has_virtual_battery = False

    await _refresh_at(coordinator, client, 0, 1000.0, 5000.0)
    data = await _refresh_at(coordinator, client, 5, 2000.0, 6000.0)

    assert (data.msb_discharge_power, data.grid_billed_power) == (None, None)


def test_coordinator__should_detect_virtual_battery_from_config_entry():
    """Detection follows the battery id stored at setup (empty when MyLight has none)."""
    with_battery, _ = _build_coordinator()
    config_entry = MagicMock()
    config_entry.options = {}
    config_entry.data = {"virtual_battery_id": ""}
    without_battery = MyLightSystemsDataUpdateCoordinator(MagicMock(), MagicMock(), config_entry)

    assert with_battery.has_virtual_battery is True
    assert without_battery.has_virtual_battery is False
