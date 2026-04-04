"""Unit tests for switch module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.mylight_systems.api.exceptions import MyLightSystemsError
from custom_components.mylight_systems.switch import MyLightSystemsSwitch, master_relay_switch


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with the attributes the switch needs."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.async_request_refresh = AsyncMock()
    coordinator.turn_on_master_relay = AsyncMock()
    coordinator.turn_off_master_relay = AsyncMock()
    coordinator.master_relay_is_on = MagicMock(return_value=False)
    return coordinator


@pytest.fixture
def switch_entity(mock_coordinator):
    """Create a MyLightSystemsSwitch backed by the mock coordinator."""
    return MyLightSystemsSwitch(
        entry_id="test_entry_id",
        coordinator=mock_coordinator,
        entity_description=master_relay_switch,
    )


# --- is_on property ---


def test_is_on__returns_false_when_relay_is_off(switch_entity, mock_coordinator):
    """is_on delegates to coordinator.master_relay_is_on() and returns False."""
    mock_coordinator.master_relay_is_on.return_value = False

    assert switch_entity.is_on is False


def test_is_on__returns_true_when_relay_is_on(switch_entity, mock_coordinator):
    """is_on delegates to coordinator.master_relay_is_on() and returns True."""
    mock_coordinator.master_relay_is_on.return_value = True

    assert switch_entity.is_on is True


def test_is_on__reflects_updated_coordinator_state(switch_entity, mock_coordinator):
    """is_on always reflects the latest state from the coordinator."""
    mock_coordinator.master_relay_is_on.return_value = False
    assert switch_entity.is_on is False

    mock_coordinator.master_relay_is_on.return_value = True
    assert switch_entity.is_on is True


# --- async_turn_on ---


@pytest.mark.asyncio
async def test_async_turn_on__happy_path(switch_entity, mock_coordinator):
    """turn_on calls the relay coroutine, requests a refresh, and marks available."""
    await switch_entity.async_turn_on()

    mock_coordinator.turn_on_master_relay.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()
    assert switch_entity._attr_available is True


@pytest.mark.asyncio
async def test_async_turn_on__api_error_sets_unavailable(switch_entity, mock_coordinator):
    """turn_on sets _attr_available=False and skips refresh on API error."""
    mock_coordinator.turn_on_master_relay.side_effect = MyLightSystemsError("relay error")

    await switch_entity.async_turn_on()

    assert switch_entity._attr_available is False
    mock_coordinator.async_request_refresh.assert_not_called()


# --- async_turn_off ---


@pytest.mark.asyncio
async def test_async_turn_off__happy_path(switch_entity, mock_coordinator):
    """turn_off calls the relay coroutine, requests a refresh, and marks available."""
    await switch_entity.async_turn_off()

    mock_coordinator.turn_off_master_relay.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()
    assert switch_entity._attr_available is True


@pytest.mark.asyncio
async def test_async_turn_off__api_error_sets_unavailable(switch_entity, mock_coordinator):
    """turn_off sets _attr_available=False and skips refresh on API error."""
    mock_coordinator.turn_off_master_relay.side_effect = MyLightSystemsError("relay error")

    await switch_entity.async_turn_off()

    assert switch_entity._attr_available is False
    mock_coordinator.async_request_refresh.assert_not_called()
