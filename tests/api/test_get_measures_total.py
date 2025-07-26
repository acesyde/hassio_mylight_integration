"""Unit tests for the get measures total API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    MEASURES_TOTAL_URL,
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
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_total/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_response_fixture():
    """Load valid response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_total/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_async_get_measures_total__should_raise_unauthorized_exception_when_invalid_token(
    api_client, unauthorized_response_fixture
):
    """Test async_get_measures_total raises UnauthorizedException with invalid token."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    url = DEFAULT_BASE_URL + MEASURES_TOTAL_URL + f"?authToken={token}&measureType={measure_type}&deviceId={device_id}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=unauthorized_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_get_measures_total(token, measure_type, device_id)

    # Then
    assert UnauthorizedError == exc_info.type


@pytest.mark.asyncio
async def test_async_get_measures_total__should_return_measures_data_when_valid_request(
    api_client, valid_response_fixture
):
    """Test async_get_measures_total returns correct measures data with valid request."""
    # Given
    token = "abcdef"  # noqa: S105
    measure_type = "one_phase"
    device_id = "qVGSJ45vkeqvrHy6g"
    url = DEFAULT_BASE_URL + MEASURES_TOTAL_URL + f"?authToken={token}&measureType={measure_type}&deviceId={device_id}"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_response_fixture,
        )

        response = await api_client.async_get_measures_total(token, measure_type, device_id)

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
        "positive_index",
        "negative_index",
        "grid_sans_msb_energy",
        "autonomy_rate",
        "available_power_rate",
        "self_conso",
    ]

    assert 14 == len(response)
    assert expected_items == [item.type for item in response]
