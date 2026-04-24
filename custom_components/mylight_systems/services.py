"""Services for MyLight Systems integration."""

from __future__ import annotations

import csv
import io
from datetime import date
from pathlib import Path

import voluptuous as vol

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError

from .api.models import Measure
from .const import CONF_GRID_TYPE, CONF_VIRTUAL_DEVICE_ID, DOMAIN, LOGGER

SERVICE_EXPORT_CSV = "export_measures_csv"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("from_date"): str,
        vol.Required("to_date"): str,
    }
)


def _parse_date(value: str, field_name: str) -> date:
    """Parse an ISO date string, raising ServiceValidationError on failure."""
    try:
        parsed = date.fromisoformat(value)
        # Strict validation: reject ISO week-date formats and other non-YYYY-MM-DD formats
        if parsed.isoformat() != value:
            raise ValueError("Format mismatch")
        return parsed
    except ValueError as exc:
        raise ServiceValidationError(
            f"Invalid date for '{field_name}': '{value}'. Use YYYY-MM-DD format."
        ) from exc


def _build_csv(rows: list[tuple[date, list[Measure]]]) -> str:
    """Build a CSV string from (date, measures) pairs.

    Columns are discovered dynamically from all rows. Missing measures for
    a given day are written as empty strings.
    """
    type_units: dict[str, str] = {}
    for _, measures in rows:
        for m in measures:
            if m.type not in type_units:
                type_units[m.type] = m.unit

    measure_types = list(type_units.keys())

    output = io.StringIO()
    writer = csv.writer(output)

    header = ["date"] + [f"{t} ({type_units[t]})" for t in measure_types]
    writer.writerow(header)

    for day, measures in rows:
        values_by_type = {m.type: m.value for m in measures}
        row = [day.isoformat()] + [values_by_type.get(t, "") for t in measure_types]
        writer.writerow(row)

    return output.getvalue()


def _write_csv(output_dir: Path, filename: str, content: str) -> Path:
    """Write CSV content to a file. Runs in an executor (blocking I/O)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register the export_measures_csv service action."""
    if hass.services.has_service(DOMAIN, SERVICE_EXPORT_CSV):
        return

    async def handle_export_csv(call: ServiceCall) -> ServiceResponse:
        from_date = _parse_date(call.data["from_date"], "from_date")
        to_date = _parse_date(call.data["to_date"], "to_date")

        # Reject same-day and backward ranges; exports require at least a one-day interval
        if from_date >= to_date:
            raise ServiceValidationError("'from_date' must be strictly before 'to_date'.")
        if to_date > date.today():
            raise ServiceValidationError("'to_date' cannot be in the future.")

        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError("No MyLight Systems config entry is loaded.")

        coordinator = entries[0].runtime_data
        email = coordinator.config_entry.data[CONF_EMAIL]
        password = coordinator.config_entry.data[CONF_PASSWORD]
        grid_type = coordinator.config_entry.data[CONF_GRID_TYPE]
        device_id = coordinator.config_entry.data[CONF_VIRTUAL_DEVICE_ID]

        await coordinator.authenticate_user(email, password)
        auth_token = coordinator.auth_token
        if auth_token is None:
            raise ServiceValidationError("Authentication failed: no token available.")

        rows = await coordinator.client.async_get_measures_grouping_range(
            auth_token, grid_type, device_id, from_date, to_date
        )

        filename = f"mylight_export_{from_date.isoformat()}_{to_date.isoformat()}.csv"
        output_dir = Path(hass.config.config_dir) / "www" / "mylight_systems"
        csv_content = _build_csv(rows)

        output_path = await hass.async_add_executor_job(
            _write_csv, output_dir, filename, csv_content
        )

        url_path = f"/local/mylight_systems/{filename}"
        LOGGER.info(
            "CSV export written to %s (%d rows, %s to %s)",
            output_path,
            len(rows),
            from_date.isoformat(),
            to_date.isoformat(),
        )
        return {"path": url_path}

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_CSV,
        handle_export_csv,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister the service when the last config entry is removed.

    Called while the entry being unloaded is still registered, so
    `async_entries` returns it. `<= 1` therefore fires exactly when
    the last entry is being removed.
    """
    remaining = hass.config_entries.async_entries(DOMAIN)
    if len(remaining) <= 1:
        hass.services.async_remove(DOMAIN, SERVICE_EXPORT_CSV)
