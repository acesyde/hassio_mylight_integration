"""Unit tests for the get grid power API."""

import aiohttp
import pytest
import pytest_asyncio

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    STATES_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import UnauthorizedError

from . import mock_get

TOKEN = "abcdef"  # noqa: S105
URL = DEFAULT_BASE_URL + STATES_URL + f"?authToken={TOKEN}"


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


def _states(value=-1500, unit="watt", meter_id="meter-1", measure_type="electric_power"):
    return {
        "status": "ok",
        "deviceStates": [
            {
                "deviceId": "other",
                "sensorStates": [{"measure": {"type": "electric_power", "value": 999, "unit": "watt"}}],
            },
            {
                "deviceId": meter_id,
                "sensorStates": [
                    {"measure": {"type": measure_type, "value": value, "unit": unit, "date": "2026-11-04 14:00:00"}}
                ],
            },
        ],
    }


@pytest.mark.asyncio
async def test_get_grid_power__should_raise_unauthorized_when_invalid_token(api_client, aresponses):
    """Not authorized responses must propagate so reauth works."""
    mock_get(aresponses, URL, {"status": "error", "error": "not.authorized"})

    with pytest.raises(UnauthorizedError):
        await api_client.async_get_grid_power(TOKEN, "meter-1")


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [1500, -1500, 0, 12.5])
async def test_get_grid_power__should_return_signed_measure(api_client, aresponses, value):
    """The signed value is returned as is, including zero."""
    mock_get(aresponses, URL, _states(value=value))

    result = await api_client.async_get_grid_power(TOKEN, "meter-1")

    assert result is not None
    assert value == result.value
    assert "watt" == result.unit


@pytest.mark.asyncio
async def test_get_grid_power__should_return_none_when_meter_not_in_states(api_client, aresponses):
    """Missing meter state is unknown."""
    mock_get(aresponses, URL, _states(meter_id="another"))

    assert await api_client.async_get_grid_power(TOKEN, "meter-1") is None


@pytest.mark.asyncio
async def test_get_grid_power__should_return_none_when_no_power_measure(api_client, aresponses):
    """A meter without an electric_power measure is unknown."""
    mock_get(aresponses, URL, _states(measure_type="electric_energy"))

    assert await api_client.async_get_grid_power(TOKEN, "meter-1") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("unit", ["W", "kW", ""])
async def test_get_grid_power__should_return_none_when_wrong_unit(api_client, aresponses, unit):
    """Only watt readings are accepted."""
    mock_get(aresponses, URL, _states(unit=unit))

    assert await api_client.async_get_grid_power(TOKEN, "meter-1") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [None, "1500", True, float("nan")])
async def test_get_grid_power__should_return_none_when_value_not_finite_number(api_client, aresponses, value):
    """Strings, booleans, null and NaN are not valid readings."""
    mock_get(aresponses, URL, _states(value=value))

    assert await api_client.async_get_grid_power(TOKEN, "meter-1") is None
