"""Unit tests for the coordinator."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

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
