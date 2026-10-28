"""Unit tests for the get schedule API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    SCHEDULE_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import MyLightSystemsError, UnauthorizedError

from . import mock_get


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
    fixture_path = os.path.normcase(dir_path + "/fixtures/schedules/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_response_fixture():
    """Load valid response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/schedules/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_get_schedule__should_raise_unauthorized_exception_when_invalid_token(
    api_client, aresponses, unauthorized_response_fixture
):
    """Test with invalid token should raise UnauthorizedException."""
    # Given
    token = "abcdef"  # noqa: S105
    schedule_type = "electric_tariff"
    url = DEFAULT_BASE_URL + SCHEDULE_URL + f"?authToken={token}&scheduleType={schedule_type}"

    # When / Then
    mock_get(aresponses, url, unauthorized_response_fixture)

    with pytest.raises(Exception) as exc_info:
        await api_client.async_get_schedule(token, schedule_type)

    assert UnauthorizedError == exc_info.type


@pytest.mark.asyncio
async def test_get_schedule__should_raise_mylight_error_when_schedule_key_missing(api_client, aresponses):
    """Test with response missing 'schedule' key should raise MyLightSystemsError."""
    # Given
    token = "abcdef"  # noqa: S105
    schedule_type = "electric_tariff"
    url = DEFAULT_BASE_URL + SCHEDULE_URL + f"?authToken={token}&scheduleType={schedule_type}"

    # When / Then
    mock_get(aresponses, url, {"status": "ok"})

    with pytest.raises(Exception) as exc_info:
        await api_client.async_get_schedule(token, schedule_type)

    assert MyLightSystemsError == exc_info.type


@pytest.mark.asyncio
async def test_get_schedule__should_return_schedule_when_valid_token(api_client, aresponses, valid_response_fixture):
    """Test with valid token should return schedule data."""
    # Given
    token = "abcdef"  # noqa: S105
    schedule_type = "electric_tariff"
    url = DEFAULT_BASE_URL + SCHEDULE_URL + f"?authToken={token}&scheduleType={schedule_type}"

    # When
    mock_get(aresponses, url, valid_response_fixture)

    response = await api_client.async_get_schedule(token, schedule_type)

    # Then
    assert response.ranges == "mon 22:20 on;tue 6:20 off"
    assert response.type == "electric_tariff"
    assert response.category == "custom"
    assert response.enabled is True
