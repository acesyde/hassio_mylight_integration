"""Unit tests for switch module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.mylight_systems.api.exceptions import MyLightSystemsError
from custom_components.mylight_systems.switch import (
    MyLightSystemsSwitch,
    async_setup_entry,
    master_relay_switch,
    water_heater_relay_switch,
)


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


# --- async_setup_entry: which switches are added depending on relay roles ---


def _make_entry(coordinator: MagicMock) -> MagicMock:
    """Build a mock config entry whose runtime_data points to the coordinator."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.runtime_data = coordinator
    return entry


def _make_setup_coordinator(*, master_id: str | None, water_heater_id: str | None) -> MagicMock:
    """Build a coordinator mock that exposes only the role helpers used by async_setup_entry."""
    coordinator = MagicMock()
    coordinator.master_relay_id = MagicMock(return_value=master_id)
    coordinator.water_heater_relay_id = MagicMock(return_value=water_heater_id)
    return coordinator


@pytest.mark.asyncio
async def test_setup__only_master_relay_creates_one_switch():
    """A coordinator with only a master relay yields a single master_relay switch."""
    coordinator = _make_setup_coordinator(master_id="sw-master", water_heater_id=None)
    entry = _make_entry(coordinator)
    add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, add_entities)

    assert add_entities.call_count == 1
    entities = list(add_entities.call_args.args[0])
    assert len(entities) == 1
    assert entities[0].entity_description.key == "master_relay"


@pytest.mark.asyncio
async def test_setup__only_water_heater_relay_creates_one_switch():
    """A coordinator with only a water-heater relay yields a single water_heater_relay switch."""
    coordinator = _make_setup_coordinator(master_id=None, water_heater_id="sw-wh")
    entry = _make_entry(coordinator)
    add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, add_entities)

    entities = list(add_entities.call_args.args[0])
    assert len(entities) == 1
    assert entities[0].entity_description.key == "water_heater_relay"


@pytest.mark.asyncio
async def test_setup__both_relays_creates_two_switches():
    """A coordinator with both roles yields both switches."""
    coordinator = _make_setup_coordinator(master_id="sw-master", water_heater_id="sw-wh")
    entry = _make_entry(coordinator)
    add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, add_entities)

    entities = list(add_entities.call_args.args[0])
    keys = {e.entity_description.key for e in entities}
    assert keys == {"master_relay", "water_heater_relay"}


@pytest.mark.asyncio
async def test_setup__no_relay_creates_no_switch():
    """A coordinator with no relay yields no switch."""
    coordinator = _make_setup_coordinator(master_id=None, water_heater_id=None)
    entry = _make_entry(coordinator)
    add_entities = MagicMock()

    await async_setup_entry(MagicMock(), entry, add_entities)

    entities = list(add_entities.call_args.args[0])
    assert entities == []


# --- water_heater_relay_switch behaviour (mirror of master_relay_switch) ---


@pytest.fixture
def mock_water_heater_coordinator():
    """Mock coordinator exposing the water-heater relay methods."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.async_request_refresh = AsyncMock()
    coordinator.turn_on_water_heater_relay = AsyncMock()
    coordinator.turn_off_water_heater_relay = AsyncMock()
    coordinator.water_heater_relay_is_on = MagicMock(return_value=False)
    return coordinator


@pytest.fixture
def water_heater_switch_entity(mock_water_heater_coordinator):
    """Build a switch wired to water_heater_relay_switch description."""
    return MyLightSystemsSwitch(
        entry_id="test_entry_id",
        coordinator=mock_water_heater_coordinator,
        entity_description=water_heater_relay_switch,
    )


def test_water_heater__is_on_delegates_to_coordinator(water_heater_switch_entity, mock_water_heater_coordinator):
    """is_on uses the water_heater coordinator method, not master."""
    mock_water_heater_coordinator.water_heater_relay_is_on.return_value = True

    assert water_heater_switch_entity.is_on is True
    mock_water_heater_coordinator.water_heater_relay_is_on.assert_called()


@pytest.mark.asyncio
async def test_water_heater__async_turn_on_calls_water_heater_coroutine(
    water_heater_switch_entity, mock_water_heater_coordinator
):
    """turn_on invokes the water_heater coroutine and refreshes."""
    await water_heater_switch_entity.async_turn_on()

    mock_water_heater_coordinator.turn_on_water_heater_relay.assert_called_once()
    mock_water_heater_coordinator.async_request_refresh.assert_called_once()
