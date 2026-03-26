"""Diagnostics support for MyLight Systems."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from . import MyLightConfigEntry
from .const import (
    CONF_MASTER_ID,
    CONF_MASTER_RELAY_ID,
    CONF_SUBSCRIPTION_ID,
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
    }
