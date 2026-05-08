"""Unit tests for coordinator wiring (role helpers + per-device grouping)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.const import (
    CONF_GMD_DEVICES,
    CONF_GRID_TYPE,
    CONF_RELAY_DEVICES,
    CONF_VIRTUAL_BATTERY_ID,
    CONF_VIRTUAL_DEVICE_ID,
)
from custom_components.mylight_systems.coordinator import MyLightSystemsDataUpdateCoordinator


def _make_coordinator(entry_data: dict) -> MyLightSystemsDataUpdateCoordinator:
    """Build a coordinator without invoking DataUpdateCoordinator.__init__.

    The role helpers only need `config_entry.data` to work, so we shortcut
    the heavy HA init and assemble the minimum surface required.
    """
    coordinator = MyLightSystemsDataUpdateCoordinator.__new__(MyLightSystemsDataUpdateCoordinator)
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.data = entry_data
    coordinator.client = MagicMock()
    coordinator._auth_lock = None
    coordinator._MyLightSystemsDataUpdateCoordinator__auth_token = "tok"  # noqa: SLF001, S105
    return coordinator


# --- role helpers ---


def test_master_relay_id__returns_first_non_water_heater_relay():
    coordinator = _make_coordinator(
        {
            CONF_RELAY_DEVICES: [
                {"id": "wh", "device_type_id": "water_heater"},
                {"id": "generic", "device_type_id": "other_device_type"},
            ],
        }
    )
    assert coordinator.master_relay_id() == "generic"


def test_master_relay_id__returns_none_when_only_water_heater():
    coordinator = _make_coordinator(
        {CONF_RELAY_DEVICES: [{"id": "wh", "device_type_id": "water_heater"}]},
    )
    assert coordinator.master_relay_id() is None


def test_water_heater_relay_id__returns_water_heater_relay():
    coordinator = _make_coordinator(
        {CONF_RELAY_DEVICES: [{"id": "wh", "device_type_id": "water_heater"}]},
    )
    assert coordinator.water_heater_relay_id() == "wh"


def test_water_heater_gmd_id__ignores_composite_gmd():
    coordinator = _make_coordinator(
        {
            CONF_GMD_DEVICES: [
                {"id": "comp", "device_type_id": "water_heater", "is_composite": True},
                {"id": "sub", "device_type_id": "water_heater", "is_composite": False},
            ],
        }
    )
    # Only the non-composite gmd is the actual sub-meter
    assert coordinator.water_heater_gmd_id() == "sub"


def test_water_heater_gmd_id__returns_none_when_absent():
    coordinator = _make_coordinator({CONF_GMD_DEVICES: []})
    assert coordinator.water_heater_gmd_id() is None


# --- _async_update_data: per-device grouping wiring ---


@pytest.mark.asyncio
async def test_update_data__sources_water_heater_energy_from_per_device_grouping():
    """`water_heater_energy` comes from measures/grouping called with the gmd id."""
    entry_data = {
        "email": "u@e.com",
        "password": "p",
        CONF_GRID_TYPE: "one_phase",
        CONF_VIRTUAL_DEVICE_ID: "vrt",
        CONF_VIRTUAL_BATTERY_ID: "bat",
        CONF_RELAY_DEVICES: [],
        CONF_GMD_DEVICES: [
            {"id": "gmd-wh", "device_type_id": "water_heater", "is_composite": False},
        ],
    }
    coordinator = _make_coordinator(entry_data)
    coordinator.authenticate_user = AsyncMock()

    # Each call returns a list of Measure as the real client would
    global_grouping = [Measure(type="produced_energy", value=42, unit="Ws")]
    per_device_grouping = [Measure(type="energy", value=3600, unit="Ws")]
    measures_total = [Measure(type="autonomy_rate", value=80.0, unit="%")]

    coordinator.client.async_get_measures_grouping = AsyncMock(side_effect=[global_grouping, per_device_grouping])
    coordinator.client.async_get_measures_total = AsyncMock(return_value=measures_total)
    coordinator.client.async_get_battery_state = AsyncMock(return_value=None)
    coordinator.client.async_get_relay_state = AsyncMock(return_value="off")

    data = await coordinator._async_update_data()  # noqa: SLF001

    # Two grouping calls happened: global + per-device
    assert coordinator.client.async_get_measures_grouping.await_count == 2
    second_call_args = coordinator.client.async_get_measures_grouping.await_args_list[1]
    # 3rd positional arg of the second call is the gmd id
    assert second_call_args.args[2] == "gmd-wh"

    # water_heater_energy is the `energy` measure from the per-device grouping
    assert data.water_heater_energy is not None
    assert data.water_heater_energy.value == 3600
    assert data.water_heater_energy.type == "energy"


@pytest.mark.asyncio
async def test_update_data__no_per_device_call_when_no_water_heater_gmd():
    """No per-device grouping call when no water-heater gmd is configured."""
    entry_data = {
        "email": "u@e.com",
        "password": "p",
        CONF_GRID_TYPE: "one_phase",
        CONF_VIRTUAL_DEVICE_ID: "vrt",
        CONF_VIRTUAL_BATTERY_ID: "bat",
        CONF_RELAY_DEVICES: [],
        CONF_GMD_DEVICES: [
            {"id": "gmd-comp", "device_type_id": None, "is_composite": True},
        ],
    }
    coordinator = _make_coordinator(entry_data)
    coordinator.authenticate_user = AsyncMock()

    coordinator.client.async_get_measures_grouping = AsyncMock(return_value=[])
    coordinator.client.async_get_measures_total = AsyncMock(return_value=[])
    coordinator.client.async_get_battery_state = AsyncMock(return_value=None)
    coordinator.client.async_get_relay_state = AsyncMock(return_value="off")

    data = await coordinator._async_update_data()  # noqa: SLF001

    # Only one grouping call (the global one)
    assert coordinator.client.async_get_measures_grouping.await_count == 1
    assert data.water_heater_energy is None
