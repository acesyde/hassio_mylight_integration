# CSV Export Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `mylight_systems.export_measures_csv` HA service action that fetches daily energy data for a user-supplied date range and returns a CSV string in the service response.

**Architecture:** A new `async_get_measures_grouping_range` client method makes one API call for the full range and returns `list[tuple[date, list[Measure]]]`. A new `services.py` registers the HA action, validates dates, calls the client, builds the CSV, and returns `{"csv": "..."}`. `__init__.py` wires setup/teardown.

**Tech Stack:** Python `csv` stdlib, `voluptuous` (already used), `aioresponses` for test mocking, `pytest-asyncio`.

---

## File Map

| File | Change |
|------|--------|
| `custom_components/mylight_systems/api/client.py` | Add `async_get_measures_grouping_range` method |
| `custom_components/mylight_systems/services.py` | New — service registration, handler, CSV builder |
| `custom_components/mylight_systems/__init__.py` | Call `async_setup_services` / `async_unload_services` |
| `tests/api/test_get_measures_grouping_range.py` | New — client method tests |
| `tests/test_services.py` | New — pure-function tests for `_parse_date` and `_build_csv` |

---

### Task 1: Add `async_get_measures_grouping_range` to the API client

**Files:**
- Modify: `custom_components/mylight_systems/api/client.py`
- Test: `tests/api/test_get_measures_grouping_range.py`

- [ ] **Step 1: Create the test file**

Create `tests/api/test_get_measures_grouping_range.py`:

```python
"""Unit tests for async_get_measures_grouping_range."""

from datetime import date

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    MEASURES_GROUPING_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import UnauthorizedError


@pytest_asyncio.fixture
async def session():
    """Create an aiohttp session for testing."""
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def api_client(session):
    """Create a MyLightApiClient instance for testing."""
    return MyLightApiClient(DEFAULT_BASE_URL, session)


def _url(token, measure_type, device_id, from_iso, to_iso):
    return (
        DEFAULT_BASE_URL
        + MEASURES_GROUPING_URL
        + f"?authToken={token}&groupType=day&fromDate={from_iso}&toDate={to_iso}"
        + f"&measureType={measure_type}&deviceId={device_id}"
    )


@pytest.mark.asyncio
async def test_range_single_day_maps_date(api_client):
    """Single-day range returns one (date, measures) tuple with correct date."""
    token = "abc"  # noqa: S105
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 1)
    url = _url(token, "one_phase", "dev1", "2025-01-01", "2025-01-02")
    payload = {
        "status": "ok",
        "measures": [
            {"values": [{"type": "produced_energy", "value": 100.0, "unit": "Ws"}]}
        ],
    }
    with aioresponses() as m:
        m.get(url, payload=payload)
        result = await api_client.async_get_measures_grouping_range(
            token, "one_phase", "dev1", from_date, to_date
        )
    assert len(result) == 1
    assert result[0][0] == date(2025, 1, 1)
    assert result[0][1][0].type == "produced_energy"
    assert result[0][1][0].value == 100.0


@pytest.mark.asyncio
async def test_range_multiple_days_maps_dates_in_order(api_client):
    """Three-day range returns three tuples with dates in order."""
    token = "abc"  # noqa: S105
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 3)
    url = _url(token, "one_phase", "dev1", "2025-01-01", "2025-01-04")
    payload = {
        "status": "ok",
        "measures": [
            {"values": [{"type": "produced_energy", "value": 10.0, "unit": "Ws"}]},
            {"values": [{"type": "produced_energy", "value": 20.0, "unit": "Ws"}]},
            {"values": [{"type": "produced_energy", "value": 30.0, "unit": "Ws"}]},
        ],
    }
    with aioresponses() as m:
        m.get(url, payload=payload)
        result = await api_client.async_get_measures_grouping_range(
            token, "one_phase", "dev1", from_date, to_date
        )
    assert len(result) == 3
    assert result[0][0] == date(2025, 1, 1)
    assert result[1][0] == date(2025, 1, 2)
    assert result[2][0] == date(2025, 1, 3)
    assert result[0][1][0].value == 10.0
    assert result[2][1][0].value == 30.0


@pytest.mark.asyncio
async def test_range_fewer_api_groups_than_days_pads_with_empty(api_client):
    """When API returns fewer groups than days, extra dates get empty measure lists."""
    token = "abc"  # noqa: S105
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 3)
    url = _url(token, "one_phase", "dev1", "2025-01-01", "2025-01-04")
    payload = {
        "status": "ok",
        "measures": [
            {"values": [{"type": "produced_energy", "value": 10.0, "unit": "Ws"}]},
        ],
    }
    with aioresponses() as m:
        m.get(url, payload=payload)
        result = await api_client.async_get_measures_grouping_range(
            token, "one_phase", "dev1", from_date, to_date
        )
    assert len(result) == 3
    assert result[0][1][0].value == 10.0
    assert result[1][1] == []
    assert result[2][1] == []


@pytest.mark.asyncio
async def test_range_empty_measures_response(api_client):
    """Empty measures list in response produces one entry per day with empty measures."""
    token = "abc"  # noqa: S105
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 2)
    url = _url(token, "one_phase", "dev1", "2025-01-01", "2025-01-03")
    payload = {"status": "ok", "measures": []}
    with aioresponses() as m:
        m.get(url, payload=payload)
        result = await api_client.async_get_measures_grouping_range(
            token, "one_phase", "dev1", from_date, to_date
        )
    assert len(result) == 2
    assert result[0][1] == []
    assert result[1][1] == []


@pytest.mark.asyncio
async def test_range_raises_unauthorized_error(api_client):
    """Unauthorized API response raises UnauthorizedError."""
    token = "abc"  # noqa: S105
    from_date = date(2025, 1, 1)
    to_date = date(2025, 1, 1)
    url = _url(token, "one_phase", "dev1", "2025-01-01", "2025-01-02")
    with aioresponses() as m:
        m.get(url, payload={"status": "error", "error": "not.authorized"})
        with pytest.raises(UnauthorizedError):
            await api_client.async_get_measures_grouping_range(
                token, "one_phase", "dev1", from_date, to_date
            )
```

- [ ] **Step 2: Run the tests — confirm they fail**

```bash
pytest tests/api/test_get_measures_grouping_range.py -v
```

Expected: all 5 tests fail with `AttributeError: 'MyLightApiClient' object has no attribute 'async_get_measures_grouping_range'`

- [ ] **Step 3: Add `date`/`timedelta` import to client.py**

Open `custom_components/mylight_systems/api/client.py`. The file currently has no `datetime` import. Add this line after the existing stdlib imports (after `import asyncio`):

```python
from datetime import date, timedelta
```

- [ ] **Step 4: Add `async_get_measures_grouping_range` method to client**

In `custom_components/mylight_systems/api/client.py`, add the following method directly after `async_get_measures_grouping` (after line ~245):

```python
    async def async_get_measures_grouping_range(
        self,
        auth_token: str,
        phase: str,
        device_id: str,
        from_date: date,
        to_date: date,
    ) -> list[tuple[date, list[Measure]]]:
        """Get device measures for an inclusive date range, one entry per day.

        Makes a single API call. The API endpoint is exclusive on toDate,
        so to_date + 1 day is passed. Groups are zipped with the generated
        date sequence; missing groups are represented as empty measure lists.
        """
        response: MeasuresGroupingResponseSchema = await self._execute_request(
            "get",
            MEASURES_GROUPING_URL,
            params={
                "authToken": auth_token,
                "groupType": "day",
                "fromDate": from_date.isoformat(),
                "toDate": (to_date + timedelta(days=1)).isoformat(),
                "measureType": phase,
                "deviceId": device_id,
            },
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "measures")

        num_days = (to_date - from_date).days + 1
        date_sequence = [from_date + timedelta(days=i) for i in range(num_days)]
        groups = response["measures"] or []

        result: list[tuple[date, list[Measure]]] = []
        for i, day in enumerate(date_sequence):
            if i < len(groups):
                measures = [
                    Measure(v["type"], v["value"], v["unit"])
                    for v in groups[i]["values"]
                ]
            else:
                measures = []
            result.append((day, measures))

        return result
```

- [ ] **Step 5: Run the tests — confirm they pass**

```bash
pytest tests/api/test_get_measures_grouping_range.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 6: Run full test suite — confirm no regressions**

```bash
pytest -v
```

Expected: all pre-existing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add custom_components/mylight_systems/api/client.py tests/api/test_get_measures_grouping_range.py
git commit -m "feat: add async_get_measures_grouping_range client method"
```

---

### Task 2: Create `services.py` with CSV builder

**Files:**
- Create: `custom_components/mylight_systems/services.py`
- Test: `tests/test_services.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_services.py`:

```python
"""Unit tests for services pure functions."""

from datetime import date

import pytest

from custom_components.mylight_systems.api.models import Measure
from custom_components.mylight_systems.services import _build_csv, _parse_date
from homeassistant.exceptions import ServiceValidationError


class TestParseDateFunction:
    def test_valid_date_string_returns_date_object(self):
        result = _parse_date("2025-01-15", "from_date")
        assert result == date(2025, 1, 15)

    def test_invalid_date_string_raises_service_validation_error(self):
        with pytest.raises(ServiceValidationError):
            _parse_date("not-a-date", "from_date")

    def test_invalid_format_raises_service_validation_error(self):
        with pytest.raises(ServiceValidationError):
            _parse_date("15/01/2025", "to_date")


class TestBuildCsvFunction:
    def test_single_day_single_measure_produces_correct_csv(self):
        rows = [(date(2025, 1, 1), [Measure("produced_energy", 100.0, "Ws")])]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert lines[0] == "date,produced_energy (Ws)"
        assert lines[1] == "2025-01-01,100.0"

    def test_multiple_days_appear_as_rows_in_order(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws")]),
            (date(2025, 1, 2), [Measure("produced_energy", 20.0, "Ws")]),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert len(lines) == 3  # header + 2 data rows
        assert lines[1].startswith("2025-01-01")
        assert lines[2].startswith("2025-01-02")

    def test_missing_measure_for_day_written_as_empty_string(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws"), Measure("grid_energy", 5.0, "Ws")]),
            (date(2025, 1, 2), [Measure("produced_energy", 20.0, "Ws")]),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        # Second row should have empty value for grid_energy
        assert lines[2].endswith(",")

    def test_column_order_matches_discovery_order(self):
        rows = [
            (
                date(2025, 1, 1),
                [
                    Measure("produced_energy", 10.0, "Ws"),
                    Measure("grid_energy", 5.0, "Ws"),
                ],
            )
        ]
        result = _build_csv(rows)
        header = result.strip().splitlines()[0]
        assert header == "date,produced_energy (Ws),grid_energy (Ws)"

    def test_empty_rows_returns_header_only(self):
        result = _build_csv([])
        lines = result.strip().splitlines()
        assert len(lines) == 1
        assert lines[0] == "date"

    def test_day_with_no_measures_writes_empty_values(self):
        rows = [
            (date(2025, 1, 1), [Measure("produced_energy", 10.0, "Ws")]),
            (date(2025, 1, 2), []),
        ]
        result = _build_csv(rows)
        lines = result.strip().splitlines()
        assert lines[2] == "2025-01-02,"
```

- [ ] **Step 2: Run the tests — confirm they fail**

```bash
pytest tests/test_services.py -v
```

Expected: all tests fail with `ModuleNotFoundError: No module named 'custom_components.mylight_systems.services'`

- [ ] **Step 3: Create `services.py`**

Create `custom_components/mylight_systems/services.py`:

```python
"""Services for MyLight Systems integration."""

from __future__ import annotations

import csv
import io
from datetime import date

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
        return date.fromisoformat(value)
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


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register the export_measures_csv service action."""
    if hass.services.has_service(DOMAIN, SERVICE_EXPORT_CSV):
        return

    async def handle_export_csv(call: ServiceCall) -> ServiceResponse:
        from_date = _parse_date(call.data["from_date"], "from_date")
        to_date = _parse_date(call.data["to_date"], "to_date")

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

        csv_content = _build_csv(rows)
        LOGGER.info(
            "CSV export generated: %d rows for %s to %s",
            len(rows),
            from_date.isoformat(),
            to_date.isoformat(),
        )
        return {"csv": csv_content}

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_CSV,
        handle_export_csv,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister the service when the last config entry is removed."""
    remaining = hass.config_entries.async_entries(DOMAIN)
    if len(remaining) <= 1:
        hass.services.async_remove(DOMAIN, SERVICE_EXPORT_CSV)
```

- [ ] **Step 4: Run the tests — confirm they pass**

```bash
pytest tests/test_services.py -v
```

Expected: all 8 tests pass.

- [ ] **Step 5: Run full test suite — confirm no regressions**

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add custom_components/mylight_systems/services.py tests/test_services.py
git commit -m "feat: add CSV export service with date validation and CSV builder"
```

---

### Task 3: Wire services into `__init__.py`

**Files:**
- Modify: `custom_components/mylight_systems/__init__.py`

- [ ] **Step 1: Update `__init__.py`**

Open `custom_components/mylight_systems/__init__.py`. The full file after changes:

```python
"""Custom integration to integrate mylight_systems with Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import DEFAULT_BASE_URL, MyLightApiClient
from .const import LOGGER, PLATFORMS
from .coordinator import MyLightSystemsDataUpdateCoordinator
from .services import async_setup_services, async_unload_services

type MyLightConfigEntry = ConfigEntry[MyLightSystemsDataUpdateCoordinator]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Set up this integration using UI."""
    session = async_get_clientsession(hass)

    client = MyLightApiClient(
        base_url=entry.data.get(CONF_URL, DEFAULT_BASE_URL),
        session=session,
    )
    coordinator = MyLightSystemsDataUpdateCoordinator(hass=hass, client=client, config_entry=entry)

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        entry.add_update_listener(lambda hass, entry: hass.config_entries.async_reload(entry.entry_id))
    )

    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Handle removal of an entry."""
    await async_unload_services(hass)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Migrate old entry data to the current version."""
    LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        LOGGER.debug("Migration to version %s successful", entry.version)
        return True

    LOGGER.error(
        "Cannot migrate config entry from version %s: unknown version. Please remove and re-add the integration.",
        entry.version,
    )
    return False
```

- [ ] **Step 2: Run full test suite — confirm no regressions**

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add custom_components/mylight_systems/__init__.py
git commit -m "feat: wire CSV export service into integration setup/teardown"
```

---

## Verification

After all tasks are complete, verify end-to-end in Home Assistant:

1. Restart HA with the updated integration.
2. Navigate to **Developer Tools → Actions**.
3. Select action `mylight_systems.export_measures_csv`.
4. Call with valid data:
   ```yaml
   from_date: "2025-01-01"
   to_date: "2025-01-03"
   ```
   Expected: response contains a `csv` key with header row + 3 data rows.
5. Call with `from_date >= to_date` — expect a validation error shown in the UI.
6. Call with `to_date` set to tomorrow — expect a validation error shown in the UI.
