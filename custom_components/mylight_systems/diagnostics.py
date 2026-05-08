"""Diagnostics support for MyLight Systems."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import asdict
from datetime import date, timedelta
from typing import Any, Callable

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from . import MyLightConfigEntry
from .api.const import (
    DEVICES_URL,
    MEASURES_GROUPING_URL,
    MEASURES_TOTAL_URL,
    PROFILE_URL,
    ROOMS_URL,
    STATES_URL,
)
from .const import (
    CONF_GMD_DEVICES,
    CONF_GRID_TYPE,
    CONF_MASTER_ID,
    CONF_RELAY_DEVICES,
    CONF_SUBSCRIPTION_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
)

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, CONF_SUBSCRIPTION_ID, CONF_MASTER_ID}


def _truncate_id(value: Any) -> Any:
    """Truncate id-like strings to first 4 chars + '***' for display."""
    if isinstance(value, str) and len(value) > 4:
        return value[:4] + "***"
    return value


def _redact_device_lists(data: dict[str, Any]) -> dict[str, Any]:
    """Truncate `id` inside relay_devices and gmd_devices lists for diagnostics."""
    for key in (CONF_RELAY_DEVICES, CONF_GMD_DEVICES):
        items = data.get(key)
        if isinstance(items, list):
            data[key] = [{**item, "id": _truncate_id(item.get("id", ""))} for item in items]
    return data


# --- Global anonymization rules (applied to all endpoints) ---

# Fields to fully replace with "***"
_REDACT_FIELDS = {"email", "firstName", "lastName", "tenant"}

# Fields to truncate to first 4 chars + "***"
_TRUNCATE_FIELDS = {"id", "deviceId", "device_id", "sensorId", "serialNumber", "masterMac", "mac"}

# Fields to zero out
_ZERO_FIELDS = {"latitude", "longitude"}

# Fields to remove entirely
_REMOVE_FIELDS = {"authToken"}

# --- Per-endpoint extra redact fields ---

_PROFILE_REDACT_FIELDS = {
    "name",
    "birthDate",
    "postalCode",
    "city",
    "address",
    "additionalAddress",
    "phoneNumber",
    "mobileNumber",
    "maintainerCode",
}

_DEVICES_REDACT_FIELDS: set[str] = set()
_MEASURES_REDACT_FIELDS: set[str] = set()
_STATES_REDACT_FIELDS: set[str] = set()
_ROOMS_REDACT_FIELDS: set[str] = set()


def _anonymize_value(key: str, value: Any, extra_redact: set[str]) -> Any:
    """Anonymize a single value based on its key."""
    if key in _REDACT_FIELDS or key in extra_redact:
        return "***"
    if key in _ZERO_FIELDS:
        return 0.0
    if key in _TRUNCATE_FIELDS and isinstance(value, str) and len(value) > 4:
        return value[:4] + "***"
    return value


def _anonymize_response(data: Any, extra_redact: set[str] | None = None) -> Any:
    """Recursively anonymize sensitive fields in an API response."""
    redact = extra_redact or set()
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in _REMOVE_FIELDS:
                continue
            result[key] = _anonymize_value(key, _anonymize_response(value, redact), redact)
        return result
    if isinstance(data, list):
        return [_anonymize_response(item, redact) for item in data]
    return data


# Each entry: (label, endpoint_path, param_builder, extra_redact_fields)
# `label` is the key used in raw_api_responses; it allows multiple entries hitting
# the same path with different params (e.g. per-gmd grouping calls).
# The callable receives (auth_token, entry_data, today, tomorrow) and returns params.
DiagnosticEndpoint = tuple[str, str, Callable[[str, dict, str, str], dict], set[str]]

DIAGNOSTIC_ENDPOINTS: list[DiagnosticEndpoint] = [
    ("profile", PROFILE_URL, lambda tok, data, t, tm: {"authToken": tok}, _PROFILE_REDACT_FIELDS),
    ("devices", DEVICES_URL, lambda tok, data, t, tm: {"authToken": tok}, _DEVICES_REDACT_FIELDS),
    (
        "measures_total",
        MEASURES_TOTAL_URL,
        lambda tok, data, t, tm: {
            "authToken": tok,
            "measureType": data[CONF_GRID_TYPE],
            "deviceId": data[CONF_VIRTUAL_DEVICE_ID],
        },
        _MEASURES_REDACT_FIELDS,
    ),
    (
        "measures_grouping",
        MEASURES_GROUPING_URL,
        lambda tok, data, t, tm: {
            "authToken": tok,
            "groupType": "day",
            "fromDate": t,
            "toDate": tm,
            "measureType": data[CONF_GRID_TYPE],
            "deviceId": data[CONF_VIRTUAL_DEVICE_ID],
        },
        _MEASURES_REDACT_FIELDS,
    ),
    ("states", STATES_URL, lambda tok, data, t, tm: {"authToken": tok}, _STATES_REDACT_FIELDS),
    ("rooms", ROOMS_URL, lambda tok, data, t, tm: {"authToken": tok}, _ROOMS_REDACT_FIELDS),
]


def _per_gmd_endpoints(entry_data: dict) -> list[DiagnosticEndpoint]:
    """Build per-gmd grouping endpoints for each gmd device declared in the entry.

    Produces self-documenting labels like
    `measures_grouping__gmd_1_water_heater_submeter` so a downloaded diagnostic
    file is easy to navigate when several gmds are present.
    """
    endpoints: list[DiagnosticEndpoint] = []
    for idx, gmd in enumerate(entry_data.get(CONF_GMD_DEVICES, []) or []):
        gmd_id = gmd.get("id")
        if not gmd_id:
            continue
        role = gmd.get("device_type_id") or "generic"
        topology = "composite" if gmd.get("is_composite") else "submeter"
        label = f"measures_grouping__gmd_{idx}_{role}_{topology}"
        endpoints.append(
            (
                label,
                MEASURES_GROUPING_URL,
                lambda tok, data, t, tm, _id=gmd_id: {
                    "authToken": tok,
                    "groupType": "day",
                    "fromDate": t,
                    "toDate": tm,
                    "measureType": data[CONF_GRID_TYPE],
                    "deviceId": _id,
                },
                _MEASURES_REDACT_FIELDS,
            )
        )
    return endpoints


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MyLightConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    integration = await async_get_integration(hass, DOMAIN)

    raw_api_responses: dict[str, str] = {}

    try:
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]

        await coordinator.authenticate_user(email, password)
        auth_token = coordinator.auth_token
        if auth_token is None:
            raise ValueError("Authentication token is not set after login")

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        entry_data = dict(entry.data)

        endpoints = list(DIAGNOSTIC_ENDPOINTS) + _per_gmd_endpoints(entry_data)

        tasks = {
            label: (
                coordinator.client.async_raw_request(
                    "get", path, params=param_builder(auth_token, entry_data, today, tomorrow)
                ),
                extra_redact,
            )
            for label, path, param_builder, extra_redact in endpoints
        }
        results = await asyncio.gather(*[coro for coro, _ in tasks.values()], return_exceptions=True)

        for (label, (_, extra_redact)), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                payload = {"error": type(result).__name__, "message": str(result)}
            else:
                payload = _anonymize_response(result, extra_redact)
            raw_api_responses[label] = base64.b64encode(json.dumps(payload, default=str).encode()).decode()

    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).debug("Failed to fetch raw API data for diagnostics", exc_info=True)

    return {
        "integration_manifest": {
            "domain": integration.domain,
            "version": integration.version,
        },
        "config_entry_data": _redact_device_lists(async_redact_data(dict(entry.data), TO_REDACT)),
        "coordinator_data": {
            k: asdict(v) if hasattr(v, "__dataclass_fields__") else v for k, v in coordinator.data._asdict().items()
        }
        if coordinator.data
        else None,
        "raw_api_responses": raw_api_responses,
    }
