"""Unit tests for the get battery state API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    STATES_URL,
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


@pytest.fixture
def unauthorized_response_fixture():
    """Load unauthorized response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/states/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_battery_response_fixture():
    """Load valid battery state response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/states/ok_battery.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def battery_not_found_response_fixture():
    """Load battery not found response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/states/ok_battery_not_found.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_get_battery_state__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test with invalid token should raise UnauthorizedException."""
    # Given
    token = "abcdef"  # noqa: S105
    battery_id = "bat-001"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(UnauthorizedError):
            await api_client.async_get_battery_state(token, battery_id)


@pytest.mark.asyncio
async def test_get_battery_state__should_return_measure_when_battery_found(api_client, valid_battery_response_fixture):
    """Test with valid token should return battery SOC measure."""
    # Given
    token = "abcdef"  # noqa: S105
    battery_id = "bat-001"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_battery_response_fixture,
        )

        response = await api_client.async_get_battery_state(token, battery_id)

    # Then
    assert response is not None
    assert "battery_soc" == response.type
    assert 75.5 == response.value
    assert "%" == response.unit


@pytest.mark.asyncio
async def test_get_battery_state__should_return_none_when_battery_not_found(
    api_client, battery_not_found_response_fixture
):
    """Test should return None when battery device is not in response."""
    # Given
    token = "abcdef"  # noqa: S105
    battery_id = "bat-001"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=battery_not_found_response_fixture,
        )

        response = await api_client.async_get_battery_state(token, battery_id)

    # Then
    assert response is None
