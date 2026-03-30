"""Unit tests for the get measures grouping API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    MEASURES_GROUPING_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import MyLightSystemsError, UnauthorizedError


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


@pytest.fixture
def unauthorized_response_fixture():
    """Load unauthorized response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_grouping/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_response_fixture():
    """Load valid response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_grouping/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


def _build_url(token, measure_type, device_id, from_date, to_date, group_type="day"):
    """Build the expected URL for the grouping endpoint."""
    return (
        DEFAULT_BASE_URL
        + MEASURES_GROUPING_URL
        + f"?authToken={token}&groupType={group_type}&fromDate={from_date}&toDate={to_date}"
        + f"&measureType={measure_type}&deviceId={device_id}"
    )


@pytest.mark.asyncio
async def test_async_get_measures_grouping__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test async_get_measures_grouping raises UnauthorizedException with invalid token."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    from_date = "2026-03-27"
    to_date = "2026-03-28"
    url = _build_url(token, measure_type, device_id, from_date, to_date)

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_measures_grouping(token, measure_type, device_id, from_date, to_date)

    # Then
    assert UnauthorizedError == exc_info.type


@pytest.mark.asyncio
async def test_async_get_measures_grouping__should_return_measures_data_when_valid_request(
    api_client, valid_response_fixture
):
    """Test async_get_measures_grouping returns correct measures data with valid request."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    from_date = "2026-03-27"
    to_date = "2026-03-28"
    url = _build_url(token, measure_type, device_id, from_date, to_date)

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_response_fixture,
        )

        response = await api_client.async_get_measures_grouping(token, measure_type, device_id, from_date, to_date)

    # Then
    expected_items = [
        "energy",
        "produced_energy",
        "electricity_meter_energy",
        "green_energy",
        "grid_energy",
        "msb_charge",
        "msb_discharge",
        "msb_loss",
        "grid_sans_msb_energy",
    ]

    assert 9 == len(response)
    assert expected_items == [item.type for item in response]


@pytest.mark.asyncio
async def test_async_get_measures_grouping__should_raise_mylight_error_when_measures_key_missing(api_client):
    """Test with response missing 'measures' key should raise MyLightSystemsError."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    from_date = "2026-03-27"
    to_date = "2026-03-28"
    url = _build_url(token, measure_type, device_id, from_date, to_date)

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload={"status": "ok"},
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_measures_grouping(token, measure_type, device_id, from_date, to_date)

    assert MyLightSystemsError == exc_info.type


@pytest.mark.asyncio
async def test_async_get_measures_grouping__should_return_empty_list_when_no_measures(
    api_client,
):
    """Test async_get_measures_grouping returns empty list when measures array is empty."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    from_date = "2026-03-27"
    to_date = "2026-03-28"
    url = _build_url(token, measure_type, device_id, from_date, to_date)

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload={"status": "ok", "measures": []},
        )

        response = await api_client.async_get_measures_grouping(token, measure_type, device_id, from_date, to_date)

    # Then
    assert 0 == len(response)
