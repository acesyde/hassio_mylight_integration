# CSV Export Service Design

**Date:** 2026-04-24
**Branch:** feature/csv-service

## Context

The MyLight Systems integration polls live energy data but offers no way to export historical data. Users who want to analyse multi-day trends currently have no access to the `/api/measures/grouping` endpoint's range capability. This service exposes that capability as a Home Assistant action that returns a CSV in the service response.

---

## Architecture

Four files are touched:

| File | Change |
|------|--------|
| `custom_components/mylight_systems/api/client.py` | Add new client method |
| `custom_components/mylight_systems/services.py` | New file — service registration & handler |
| `custom_components/mylight_systems/__init__.py` | Wire service setup/teardown |
| `custom_components/mylight_systems/const.py` | Add service name constant |

---

## Components

### 1. New client method — `async_get_measures_grouping_range`

**File:** `custom_components/mylight_systems/api/client.py`

```python
async def async_get_measures_grouping_range(
    self,
    auth_token: str,
    phase: str,
    device_id: str,
    from_date: date,
    to_date: date,
) -> list[tuple[date, list[Measure]]]:
```

- Accepts inclusive `from_date` and `to_date` (Python `date` objects).
- Formats them as ISO strings for the API; passes `to_date + 1 day` as `toDate` because the API endpoint is exclusive on the upper bound (confirmed by coordinator usage: `today` → `tomorrow` yields today's group).
- Makes a single GET to `/api/measures/grouping` with `groupType=day`.
- Generates the expected date sequence: `[from_date, from_date+1, ..., to_date]`.
- Zips the date sequence with `response["measures"]` groups.
- Returns `list[tuple[date, list[Measure]]]`. If the API returns fewer groups than expected dates, remaining dates get an empty measure list.

### 2. Service handler — `services.py`

**File:** `custom_components/mylight_systems/services.py` (new)

Registers one HA action: `mylight_systems.export_measures_csv`.

**Service call schema (voluptuous):**

```yaml
from_date: "2025-01-01"   # required, YYYY-MM-DD string
to_date:   "2025-01-31"   # required, YYYY-MM-DD string
```

**Validation (raises `ServiceValidationError`):**
- `from_date` and `to_date` parse as valid dates.
- `from_date < to_date` (strictly less than).
- `to_date <= date.today()` (not in the future).

**Handler logic:**
1. Parse dates.
2. Validate.
3. Retrieve the coordinator via `hass.config_entries.async_entries(DOMAIN)[0].runtime_data` (standard HA pattern; raises `ServiceValidationError` if no entries loaded).
4. Authenticate via `coordinator.authenticate_user(email, password)`.
5. Call `client.async_get_measures_grouping_range(auth_token, grid_type, device_id, from_date, to_date)`.
6. Build CSV string (see format below).
7. Return `{"csv": csv_string}`.

**Registration guard:** `async_setup_services` checks `hass.services.has_service(DOMAIN, SERVICE_EXPORT_CSV)` before registering, preventing double-registration when multiple config entries exist.

**Unload guard:** `async_unload_services` only unregisters the service when no remaining loaded entries exist for the domain (checked via `hass.config_entries.async_entries(DOMAIN)`).

### 3. CSV format

```
date,produced_energy (Wh),grid_energy (Wh),grid_sans_msb_energy (Wh),msb_charge (Wh),msb_discharge (Wh),green_energy (Wh),water_heater_energy (Wh),autonomy_rate (%),self_conso (%)
2025-01-01,100.5,50.2,45.1,10.3,8.7,95.2,20.1,82.0,78.5
2025-01-02,98.1,48.0,43.0,9.5,7.9,93.0,19.5,80.5,76.0
```

- Columns are the fixed set of known measure types (all 9).
- Units are inferred from the first non-null value seen per measure type; defaulting to empty string if no data exists.
- Missing measures for a day are written as empty string (not zero).
- Uses Python's `csv` stdlib module.

### 4. `__init__.py` wiring

```python
from .services import async_setup_services, async_unload_services

async def async_setup_entry(hass, entry):
    ...
    await async_setup_services(hass, entry)
    return True

async def async_unload_entry(hass, entry):
    await async_unload_services(hass)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

---

## Data Flow

```
Service call (from_date, to_date)
  → Validate dates
  → coordinator.authenticate_user()
  → client.async_get_measures_grouping_range()
      → Single GET /api/measures/grouping
      → Zip response groups with date sequence
      → Return list[tuple[date, list[Measure]]]
  → Build CSV rows
  → Return {"csv": "..."}
```

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Invalid date string | `ServiceValidationError` |
| `from_date >= to_date` | `ServiceValidationError` |
| `to_date > today` | `ServiceValidationError` |
| API / auth error | Exception propagates to HA (shown in UI) |
| API returns fewer groups than days | Missing days get empty measure values |

---

## Verification

1. **Unit tests** — test date validation logic and CSV building in isolation (no API call needed).
2. **Developer Tools** — call the action from HA → Developer Tools → Actions with a valid and invalid date range; confirm response contains `csv` key and error is shown for bad input.
3. **Existing tests** — run `pytest` to confirm no regressions in coordinator or client tests.
