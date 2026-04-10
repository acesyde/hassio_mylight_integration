"""Unit tests for the get rooms API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    ROOMS_URL,
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
    fixture_path = os.path.normcase(dir_path + "/fixtures/rooms/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_response_fixture():
    """Load valid response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/rooms/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_get_rooms__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test with invalid token should raise UnauthorizedException."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + ROOMS_URL + f"?authToken={token}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_rooms(token)

    assert UnauthorizedError == exc_info.type


@pytest.mark.asyncio
async def test_get_rooms__should_raise_mylight_error_when_rooms_key_missing(api_client):
    """Test with response missing 'rooms' key should raise MyLightSystemsError."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + ROOMS_URL + f"?authToken={token}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload={"status": "ok"},
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_rooms(token)

    assert MyLightSystemsError == exc_info.type


@pytest.mark.asyncio
async def test_get_rooms__should_return_rooms_when_valid_token(api_client, valid_response_fixture):
    """Test with valid token should return rooms with devices."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + ROOMS_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_response_fixture,
        )

        response = await api_client.async_get_rooms(token)

    # Then
    assert len(response) == 1
    room = response[0]
    assert room.id == "ab150cDfefghij"
    assert room.name == "Habitation"
    assert room.type == "alaska_home"
    assert len(room.devices) == 8
    assert room.devices[0].device_id == "ZEdtSVQKto8T53RWa_msb"
    assert room.devices[0].ecn_type == "bat"
    assert room.devices[1].device_id == "qVGSJ45vkeqvrHy6g"
    assert room.devices[1].ecn_type == "vrt"
