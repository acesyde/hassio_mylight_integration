"""Tests for MyLight Systems integration init (setup, unload, migrate)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.mylight_systems import async_migrate_entry
from custom_components.mylight_systems.const import (
    CONF_GMD_DEVICES,
    CONF_MASTER_RELAY_ID,
    CONF_RELAY_DEVICES,
)


def _make_v1_entry(data: dict) -> MagicMock:
    """Build a mock ConfigEntry at version 1 with the given data."""
    entry = MagicMock()
    entry.version = 1
    entry.data = dict(data)
    entry.entry_id = "entry_id_v1"
    return entry


def _make_hass_with_capture() -> tuple[MagicMock, list[dict]]:
    """Return (hass mock, list capturing async_update_entry calls)."""
    captured: list[dict] = []
    hass = MagicMock()

    def capture(entry, *, data, version):
        captured.append({"entry": entry, "data": data, "version": version})
        entry.data = data
        entry.version = version

    hass.config_entries.async_update_entry = MagicMock(side_effect=capture)
    return hass, captured


@pytest.mark.asyncio
async def test_async_migrate_entry__v1_with_master_relay_id_to_v2():
    """A v1 entry with a relay id is migrated to v2 with a single-element relay_devices list."""
    entry = _make_v1_entry(
        {
            CONF_MASTER_RELAY_ID: "sw-existing",
            "email": "user@example.com",
            "subscription_id": "sub42",
        }
    )
    hass, captured = _make_hass_with_capture()

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert len(captured) == 1
    new_data = captured[0]["data"]
    assert captured[0]["version"] == 2
    assert CONF_MASTER_RELAY_ID not in new_data
    assert new_data[CONF_RELAY_DEVICES] == [
        {"id": "sw-existing", "name": "", "device_type_id": None, "type_override": None},
    ]
    assert new_data[CONF_GMD_DEVICES] == []
    # untouched fields
    assert new_data["email"] == "user@example.com"
    assert new_data["subscription_id"] == "sub42"


@pytest.mark.asyncio
async def test_async_migrate_entry__v1_without_master_relay_id_to_v2():
    """A v1 entry without a relay id is migrated to v2 with empty lists."""
    entry = _make_v1_entry({"email": "user@example.com"})
    hass, captured = _make_hass_with_capture()

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert len(captured) == 1
    new_data = captured[0]["data"]
    assert captured[0]["version"] == 2
    assert new_data[CONF_RELAY_DEVICES] == []
    assert new_data[CONF_GMD_DEVICES] == []


@pytest.mark.asyncio
async def test_async_migrate_entry__v1_with_null_master_relay_id_to_v2():
    """A v1 entry with master_relay_id explicitly set to None is migrated to empty lists."""
    entry = _make_v1_entry({CONF_MASTER_RELAY_ID: None})
    hass, captured = _make_hass_with_capture()

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert captured[0]["data"][CONF_RELAY_DEVICES] == []


@pytest.mark.asyncio
async def test_async_migrate_entry__future_version_returns_false():
    """A future entry version (3+) is rejected; nothing is updated."""
    entry = _make_v1_entry({})
    entry.version = 3
    hass, captured = _make_hass_with_capture()

    result = await async_migrate_entry(hass, entry)

    assert result is False
    assert captured == []
