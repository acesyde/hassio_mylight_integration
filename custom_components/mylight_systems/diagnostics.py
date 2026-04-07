"""Diagnostics support for MyLight Systems."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import date, timedelta
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from . import MyLightConfigEntry
from .const import (
    CONF_GRID_TYPE,
    CONF_MASTER_ID,
    CONF_MASTER_RELAY_ID,
    CONF_SUBSCRIPTION_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
)

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, CONF_SUBSCRIPTION_ID, CONF_MASTER_ID, CONF_MASTER_RELAY_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MyLightConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    integration = await async_get_integration(hass, DOMAIN)

    measures_grouping_data: list | None = None
    measures_total_data: list | None = None

    try:
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
        grid_type = entry.data[CONF_GRID_TYPE]
        device_id = entry.data[CONF_VIRTUAL_DEVICE_ID]

        await coordinator.authenticate_user(email, password)
        auth_token = coordinator.auth_token

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        grouping_measures, total_measures = await asyncio.gather(
            coordinator.client.async_get_measures_grouping(
                auth_token, grid_type, device_id, from_date=today, to_date=tomorrow
            ),
            coordinator.client.async_get_measures_total(auth_token, grid_type, device_id),
        )
        measures_grouping_data = [
            {"type": m.type, "value": m.value, "unit": m.unit} for m in grouping_measures
        ]
        measures_total_data = [
            {"type": m.type, "value": m.value, "unit": m.unit} for m in total_measures
        ]
    except Exception:  # noqa: BLE001
        pass  # diagnostics must always be downloadable; sections remain None

    return {
        "integration_manifest": {
            "domain": integration.domain,
            "version": integration.version,
        },
        "config_entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "coordinator_data": {
            k: asdict(v) if hasattr(v, "__dataclass_fields__") else v for k, v in coordinator.data._asdict().items()
        }
        if coordinator.data
        else None,
        "measures_grouping": measures_grouping_data,
        "measures_total": measures_total_data,
    }
