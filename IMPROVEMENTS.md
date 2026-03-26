# MyLight Systems Integration - Improvement Analysis

> Analysis date: 2026-03-26
> Overall quality: Good - solid foundation with room for modernization

---

## BUGS

### 1. ~~`master_report_period` setter missing `else` branch~~ DONE
**File:** `custom_components/mylight_systems/api/models.py:66-70`
```python
# Current (buggy): always overwrites with value, even when None
if value is None:
    self.__master_report_period = 60
self.__master_report_period = value  # <-- runs even when value is None

# Fix: add return or else
if value is None:
    self.__master_report_period = 60
    return
self.__master_report_period = value
```

### 2. ~~`switch.is_on` double invocation~~ DONE
**File:** `custom_components/mylight_systems/switch.py:29,68`

`is_on_fn` lambda returns `coordinator.master_relay_is_on` (a method reference), then `is_on` property calls `()` on it. This works by accident because the lambda returns the bound method and the property calls it. However, the type annotation says `Callable[..., bool]` — meaning it should return a bool directly, not a callable. The code works but the type is misleading.

### 3. ~~`datetime.utcnow()` is deprecated~~ DONE

**File:** `custom_components/mylight_systems/coordinator.py:119,122`

`datetime.utcnow()` was deprecated in Python 3.12. Use `datetime.now(timezone.utc)` instead.

### 4. Broad exception catch swallows all errors
**File:** `custom_components/mylight_systems/api/client.py:69-76`
```python
except (
    asyncio.TimeoutError,
    aiohttp.ClientError,
    socket.gaierror,
    Exception,  # <-- catches EVERYTHING, including programming errors
) as exception:
```
The `Exception` catch makes the specific catches above it pointless and will silently convert bugs (e.g. `KeyError`, `TypeError`) into `CommunicationError`. Remove `Exception` from the tuple.

### 5. ~~Auth token passed as query parameter~~ N/A

MyLight API requires query parameters for auth — this is a provider limitation, not something we can change.

---

## HOME ASSISTANT BEST PRACTICES

### 6. ~~Use `ConfigEntry.runtime_data` instead of `hass.data`~~ DONE

**Priority:** High
**File:** `custom_components/mylight_systems/__init__.py:27`

Since HA 2024.x, the recommended pattern is to use typed `ConfigEntry.runtime_data` instead of `hass.data[DOMAIN][entry.entry_id]`. This provides type safety and automatic cleanup on unload.

```python
# Define a type alias
type MyLightConfigEntry = ConfigEntry[MyLightSystemsDataUpdateCoordinator]

# In async_setup_entry:
entry.runtime_data = coordinator

# In platforms:
coordinator = entry.runtime_data
```

This eliminates `DATA_COORDINATOR`, the `hass.data` dict, and manual cleanup in `async_unload_entry`.

### 7. Don't set `entity_id` manually
**Priority:** High
**Files:** `sensor.py:190`, `switch.py:61`

```python
self.entity_id = f"{DOMAIN}.{entity_description.key}"  # Don't do this
```

Home Assistant generates `entity_id` automatically from the device name and entity name. Manually setting it breaks user customization and multi-instance support (two config entries would collide). Remove these lines entirely.

### 8. Entity `name` should use `has_entity_name = True` + `translation_key`
**Priority:** High
**Files:** `sensor.py`, `switch.py`, `entity.py`

Modern HA integrations should set `has_entity_name = True` on the base entity and use `translation_key` on entity descriptions instead of hardcoded `name` strings. This enables proper localization and produces entity names like "MyLight Systems Solar production" automatically.

```python
# entity.py
class IntegrationMyLightSystemsEntity(CoordinatorEntity):
    _attr_has_entity_name = True

# sensor.py - use translation_key instead of name
MyLightSensorEntityDescription(
    key="total_solar_production",
    translation_key="total_solar_production",
    # name="Solar power production",  # Remove this
    ...
)
```

Then add entity translations in `strings.json`:
```json
{
  "entity": {
    "sensor": {
      "total_solar_production": { "name": "Solar power production" }
    }
  }
}
```

### 9. ~~Missing `strings.json` (root-level)~~ DONE

**Priority:** Medium

HA expects `strings.json` at the integration root (alongside `manifest.json`) as the source of truth for translations. The `translations/` folder is auto-generated from `strings.json`. Currently only `translations/*.json` files exist.

### 10. ~~`CONNECTION_CLASS` is deprecated~~ DONE

**Priority:** Medium
**File:** `custom_components/mylight_systems/config_flow.py:34`

```python
CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL  # Deprecated
```
This was replaced by `iot_class` in `manifest.json` (which you already have). Remove this line.

### 11. ~~`FlowResult` is deprecated~~ DONE

**Priority:** Low
**File:** `custom_components/mylight_systems/config_flow.py:39,113`

Use `ConfigFlowResult` instead of `config_entries.FlowResult` (deprecated since 2024.x).

### 12. ~~Missing `async_migrate_entry`~~ DONE

**Priority:** Low

With `VERSION = 1` you're fine now, but consider adding migration support before you need to change the config schema.

### 13. ~~Coordinator should receive `config_entry` in constructor~~ DONE

**Priority:** Medium
**File:** `custom_components/mylight_systems/coordinator.py:59-71`

The coordinator accesses `self.config_entry` but never explicitly receives it. It relies on `DataUpdateCoordinator` setting it implicitly via `config_entry` parameter. Pass it explicitly:

```python
def __init__(self, hass, client, config_entry):
    self.client = client
    super().__init__(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=SCAN_INTERVAL_IN_MINUTES),
        config_entry=config_entry,  # Explicit is better than implicit
    )
```

### 14. ~~Switch doesn't recover availability~~ DONE
**Priority:** Medium
**File:** `custom_components/mylight_systems/switch.py:75-86`

When a switch operation fails, `_attr_available` is set to `False` but never restored to `True`. The entity stays unavailable until HA restarts. Add recovery logic:

```python
async def async_turn_on(self, **kwargs):
    try:
        await self.entity_description.turn_on_fn(self.coordinator)()
        await self.coordinator.async_request_refresh()
        self._attr_available = True  # Restore on success
    except MyLightSystemsError:
        ...
```

---

## CODE QUALITY

### 15. ~~Models should use `dataclass` or `NamedTuple`~~ DONE
**Priority:** Medium
**File:** `custom_components/mylight_systems/api/models.py`

The manual property/setter pattern is verbose boilerplate. Use `@dataclass`:

```python
@dataclass
class Login:
    auth_token: str

@dataclass
class Measure:
    type: str
    value: float
    unit: str

@dataclass
class InstallationDevices:
    master_id: str = ""
    master_report_period: int = 60
    virtual_device_id: str = ""
    virtual_battery_id: str = ""
    master_relay_id: str | None = None
```

This reduces ~126 lines to ~25 lines with the same functionality.

### 16. ~~Sensor mixin pattern is outdated~~ DONE
**Priority:** Low
**File:** `custom_components/mylight_systems/sensor.py:27-39`

The `RequiredKeysMixin` + multiple inheritance pattern was common before Python 3.10. Modern approach:

```python
@dataclass(frozen=True, kw_only=True)
class MyLightSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[MyLightSystemsCoordinatorData], int | float | str | None]
```

Single class, no mixin needed.

### 17. ~~`any` (lowercase) return type~~ DONE

**Priority:** Low
**File:** `custom_components/mylight_systems/api/client.py:49`

```python
) -> any:  # Should be -> Any (from typing)
```

### 18. ~~Stale docstrings from template~~ DONE

**Priority:** Low
**Files:**
- `entity.py:1` — `"""BlueprintEntity class."""`
- `entity.py:13` — `"""BlueprintEntity class."""`
- `sensor.py:1` — `"""Sensor platform for integration_blueprint."""`
- `client.py:1` — `"""WeatherFlow Data Wrapper."""`

These are leftover from the integration blueprint template and should reference MyLight Systems.

### 19. ~~`virtual_battery_capacity` set but never exposed~~ DONE

**File:** `custom_components/mylight_systems/api/client.py:137`

```python
model.virtual_battery_capacity = device["batteryCapacity"]  # No property exists on the model
```

This silently sets an attribute that isn't defined on `InstallationDevices`. Either add it to the model or remove the line.

### 20. ~~Unit conversion magic numbers~~ DONE

**File:** `custom_components/mylight_systems/sensor.py`

`36e2` (3600) and `1e3` (1000) appear repeatedly in value lambdas. Extract to named constants:

```python
WS_TO_WH = 3600  # Watt-seconds to Watt-hours
W_TO_KW = 1000
```

---

## TESTING

### 21. Missing test coverage for critical paths
**Priority:** High

Currently tested:
- API client methods (login, profile, devices, measures)
- Sensor calculation helper

**Not tested:**
- `config_flow.py` — no tests for user flow, reconfigure, or error paths
- `coordinator.py` — no tests for token refresh, auth failure handling, data mapping
- `switch.py` — no tests for turn on/off, error handling, availability
- `__init__.py` — no tests for setup/unload lifecycle
- Integration tests with `pytest-homeassistant-custom-component`

Config flow and coordinator are the most critical to cover.

### 22. No `conftest.py` with HA fixtures
**Priority:** Medium

The test suite doesn't use `pytest-homeassistant-custom-component` which provides essential fixtures (`hass`, `mock_config_entry`, `enable_custom_integrations`). This would enable proper integration testing.

### 23. ~~Missing `test_get_battery_state.py` and `test_get_relay_state.py`~~ DONE

**Priority:** Medium

API client methods `async_get_battery_state` and `async_get_relay_state` have no tests.

---

## MANIFEST & METADATA

### 24. ~~`hacs.json` minimum HA version is very old~~ DONE

**File:** `hacs.json`

```json
"homeassistant": "2023.1.0"
```

But `pyproject.toml` requires `homeassistant >= 2025.7.0`. These should be aligned. Update `hacs.json` to match.

### 25. ~~Missing `requirements` in `manifest.json`~~ SKIPPED

All runtime dependencies (`aiohttp`, `yarl`, `async-timeout`) are already bundled with HA core. `requests` is listed in `pyproject.toml` but never imported — can be removed separately.

### 26. ~~Missing `integration_type` in `manifest.json`~~ DONE
**Priority:** Low

Consider adding `"integration_type": "hub"` to `manifest.json` for clarity (default is `hub` but being explicit is better).

---

## SECURITY

### 27. ~~Password stored in plain text in config entry~~ N/A

MyLight API only supports email/password authentication — no OAuth2 or long-lived tokens available.

### 28. ~~Login credentials sent as GET query parameters~~ N/A

MyLight API requires credentials as GET query parameters — provider limitation.

---

## FEATURES TO CONSIDER

### 29. ~~Add diagnostics support~~ DONE

Created `diagnostics.py` with email/password redaction:
```python
async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "data": coordinator.data._asdict(),
        "config": async_redact_data(entry.data, {"password", "email"}),
    }
```

### 30. Add options flow
Allow users to configure scan interval, enable/disable specific sensors, etc., without reconfiguring the whole integration.

### 31. ~~Add `reauthentication` flow~~ DONE
**Priority:** Medium

Added `async_step_reauth` and `async_step_reauth_confirm` to the config flow. When the coordinator raises `ConfigEntryAuthFailed`, users can now re-enter their password from the UI.

### 32. ~~Add energy dashboard compatibility~~ DONE

Added `suggested_display_precision=2` to all sensor entity descriptions for cleaner dashboard display.

### 33. ~~Missing `icons.json`~~ DONE

Added `icons.json` with all sensor and switch icons. Removed hardcoded `icon=` attributes from entity descriptions.

---

## SUMMARY TABLE

| # | Category | Priority | Effort | Description |
|---|----------|----------|--------|-------------|
| 1 | Bug | Critical | Low | ~~`master_report_period` setter missing else~~ DONE |
| 2 | Bug | Low | Low | ~~Switch `is_on_fn` type mismatch~~ DONE |
| 3 | Bug | Medium | Low | ~~`datetime.utcnow()` deprecated~~ DONE |
| 4 | Bug | High | Low | Broad `Exception` catch hides real errors |
| 5 | Security | Medium | N/A | ~~Auth token in query params~~ N/A (provider limitation) |
| 6 | HA Best Practice | High | Medium | ~~Use `runtime_data` instead of `hass.data`~~ DONE |
| 7 | HA Best Practice | High | Low | Remove manual `entity_id` assignment |
| 8 | HA Best Practice | High | Medium | Use `has_entity_name` + `translation_key` |
| 9 | HA Best Practice | Medium | Low | ~~Add root `strings.json`~~ DONE |
| 10 | HA Best Practice | Medium | Low | ~~Remove deprecated `CONNECTION_CLASS`~~ DONE |
| 11 | HA Best Practice | Low | Low | ~~Use `ConfigFlowResult`~~ DONE |
| 12 | HA Best Practice | Low | Low | ~~Add migration entry stub~~ DONE |
| 13 | HA Best Practice | Medium | Low | ~~Pass `config_entry` to coordinator explicitly~~ DONE |
| 14 | HA Best Practice | Medium | Low | ~~Switch availability recovery~~ DONE |
| 15 | Code Quality | Medium | Medium | ~~Use dataclasses for models~~ DONE |
| 16 | Code Quality | Low | Low | ~~Remove mixin pattern~~ DONE |
| 17 | Code Quality | Low | Low | ~~Fix `any` → `Any` type hint~~ DONE |
| 18 | Code Quality | Low | Low | ~~Fix stale template docstrings~~ DONE |
| 19 | Code Quality | Low | Low | ~~Fix `virtual_battery_capacity` ghost attribute~~ DONE |
| 20 | Code Quality | Low | Low | ~~Extract unit conversion constants~~ DONE |
| 21 | Testing | High | High | Add config_flow, coordinator, switch tests |
| 22 | Testing | Medium | Medium | Add `pytest-homeassistant-custom-component` |
| 23 | Testing | Medium | Low | ~~Add missing API client tests~~ DONE |
| 24 | Metadata | Medium | Low | ~~Align `hacs.json` min HA version~~ DONE |
| 25 | Metadata | Low | Low | ~~Add `requirements` to manifest~~ SKIPPED |
| 26 | Metadata | Low | Low | ~~Add `integration_type` to manifest~~ DONE |
| 27 | Security | Medium | N/A | ~~Password in plain text~~ N/A (provider limitation) |
| 28 | Security | Medium | N/A | ~~Credentials as GET params~~ N/A (provider limitation) |
| 29 | Feature | Low | Medium | ~~Add diagnostics support~~ DONE |
| 30 | Feature | Low | Medium | Add options flow |
| 31 | Feature | Medium | Medium | ~~Add reauth flow~~ DONE |
| 32 | Feature | Low | Low | ~~Add `suggested_display_precision`~~ DONE |
| 33 | Feature | Low | Low | ~~Add `icons.json`~~ DONE |
