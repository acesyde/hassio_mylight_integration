"""Unit tests for the get devices API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    DEVICES_URL,
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
    fixture_path = os.path.normcase(dir_path + "/fixtures/devices/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_response_fixture():
    """Load valid response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/devices/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_get_devices__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test with invalid token should raise UnauthorizedException."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + DEVICES_URL + f"?authToken={token}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_devices(token)

    assert UnauthorizedError == exc_info.type


@pytest.mark.asyncio
async def test_get_devices__should_return_device_data_when_valid_token(api_client, valid_response_fixture):
    """Test with valid token should return device data."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + DEVICES_URL + f"?authToken={token}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_response_fixture,
        )

        response = await api_client.async_get_devices(token)

    # Then
    assert "4tGrXr2CViF8chJEd" == response.master_id
    assert 300 == response.master_report_period
    assert "qVGSJ45vkeqvrHy6g" == response.virtual_device_id
    assert "ZEdtSVQKto8T53RWa_msb" == response.virtual_battery_id
