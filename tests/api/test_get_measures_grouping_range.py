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
