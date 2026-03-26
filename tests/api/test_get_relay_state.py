"""Unit tests for the get relay state API."""

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
def valid_relay_response_fixture():
    """Load valid relay state response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/states/ok_relay.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_get_relay_state__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test with invalid token should raise UnauthorizedException."""
    # Given
    token = "abcdef"  # noqa: S105
    relay_id = "relay-001"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(UnauthorizedError):
            await api_client.async_get_relay_state(token, relay_id)


@pytest.mark.asyncio
async def test_get_relay_state__should_return_state_when_relay_found(api_client, valid_relay_response_fixture):
    """Test with valid token should return relay state."""
    # Given
    token = "abcdef"  # noqa: S105
    relay_id = "relay-001"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_relay_response_fixture,
        )

        response = await api_client.async_get_relay_state(token, relay_id)

    # Then
    assert "on" == response


@pytest.mark.asyncio
async def test_get_relay_state__should_return_none_when_relay_not_found(api_client, valid_relay_response_fixture):
    """Test should return None when relay device is not in response."""
    # Given
    token = "abcdef"  # noqa: S105
    relay_id = "unknown-relay"
    url = DEFAULT_BASE_URL + STATES_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_relay_response_fixture,
        )

        response = await api_client.async_get_relay_state(token, relay_id)

    # Then
    assert response is None
