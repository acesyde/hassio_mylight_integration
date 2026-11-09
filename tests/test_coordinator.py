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


def _counters(**wh):
    """Daily counters as MyLight returns them (Ws), from Wh keyword values."""
    types = {
        "produced": "produced_energy",
        "green": "green_energy",
        "grid": "grid_energy",
        "billed": "grid_sans_msb_energy",
        "charge": "msb_charge",
        "discharge": "msb_discharge",
    }
    return [Measure(types[name], value * 3600, "watt_second") for name, value in wh.items()]


def _paris(day, hour, minute):
    return datetime(2025, 1, day, hour, minute, tzinfo=ZoneInfo("Europe/Paris"))


async def _refresh_at(coordinator, client, at, **wh):
    client.async_get_measures_grouping.return_value = _counters(**wh)
    with (
        patch.object(coordinator, "authenticate_user", AsyncMock()),
        patch("homeassistant.util.dt.utcnow", return_value=at),
        patch("homeassistant.util.dt.now", return_value=at),
    ):
        return await coordinator._async_update_data()


# Over 5 minutes (1/12 h), a counter rising by X Wh means 12 * X W.
MORNING = {"produced": 1000, "green": 600, "grid": 2000, "billed": 1500, "charge": 400, "discharge": 500}
FIVE_MIN_LATER = {"produced": 1100, "green": 650, "grid": 2010, "billed": 2010, "charge": 450, "discharge": 500}


@pytest.mark.asyncio
async def test_update__should_derive_every_power_from_counter_deltas_with_virtual_battery():
    """Each power is its counter delta over the elapsed time; unknown until two readings exist."""
    coordinator, client = _build_coordinator(meter_id=None)

    first = await _refresh_at(coordinator, client, _paris(2, 12, 0), **MORNING)
    second = await _refresh_at(coordinator, client, _paris(2, 12, 5), **FIVE_MIN_LATER)

    assert {} == first.powers
    assert second.powers == pytest.approx(
        {
            "solar_power": 1200,  # +100 Wh
            "consumption_power": 720,  # green +50 Wh, grid +10 Wh
            "grid_returned_power": 0,  # produced - green - charge stays 0
            "grid_net_power": 6120,  # billed +510 Wh, nothing returned
            "msb_charge_power": 600,
            "msb_discharge_power": 0,
            "msb_net_power": -600,  # charging: out of the home
            "grid_billed_power": 6120,
        }
    )


@pytest.mark.asyncio
async def test_update__should_use_total_import_and_skip_battery_powers_without_virtual_battery():
    """Without a virtual battery the whole grid import is grid power and no battery power exists."""
    coordinator, client = _build_coordinator(meter_id=None)
    coordinator.has_virtual_battery = False

    await _refresh_at(coordinator, client, _paris(2, 12, 0), produced=1000, green=600, grid=2000)
    data = await _refresh_at(coordinator, client, _paris(2, 12, 5), produced=1100, green=650, grid=2010)

    assert data.powers == pytest.approx(
        {
            "solar_power": 1200,
            "consumption_power": 720,
            "grid_returned_power": 600,  # +50 Wh exported
            "grid_net_power": 120 - 600,  # import 10 Wh, export 50 Wh: net export
        }
    )


@pytest.mark.asyncio
async def test_update__should_count_only_post_reset_energy_after_midnight():
    """A daily counter that went down on a new local day restarted at midnight: only its new value counts."""
    coordinator, client = _build_coordinator(meter_id=None)

    await _refresh_at(coordinator, client, _paris(1, 23, 55), billed=9000, discharge=9000)
    data = await _refresh_at(coordinator, client, _paris(2, 0, 0), billed=50, discharge=0)

    assert data.powers["grid_billed_power"] == pytest.approx(600)
    assert data.powers["msb_discharge_power"] == 0


@pytest.mark.asyncio
async def test_update__should_ignore_float_noise_decrease_within_the_same_day():
    """MyLight sometimes returns the same counter a few 1e-9 Ws lower: that is 0 W, not a midnight reset."""
    coordinator, client = _build_coordinator(meter_id=None)

    await _refresh_at(coordinator, client, _paris(2, 15, 5), billed=7953.415)
    data = await _refresh_at(coordinator, client, _paris(2, 15, 10), billed=7953.415 - 1e-12)

    assert data.powers["grid_billed_power"] == 0


def test_coordinator__should_detect_virtual_battery_from_config_entry():
    """Detection follows the battery id stored at setup (empty when MyLight has none)."""
    with_battery, _ = _build_coordinator()
    config_entry = MagicMock()
    config_entry.options = {}
    config_entry.data = {"virtual_battery_id": ""}
    without_battery = MyLightSystemsDataUpdateCoordinator(MagicMock(), MagicMock(), config_entry)

    assert with_battery.has_virtual_battery is True
    assert without_battery.has_virtual_battery is False
