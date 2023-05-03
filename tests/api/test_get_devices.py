"""Unit tests for the get devices API."""
import json

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    DEVICES_URL,
    MyLightApiClient,
    UnauthorizedException,
)


@pytest.mark.asyncio
async def test_get_devices_with_invalid_token_should_throw_exception():
    """Test with valid location data."""
    with open(
        "tests/api/fixtures/devices/unauthorized.json", encoding="utf-8"
    ) as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + DEVICES_URL + "?authToken=abcdef"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_get_devices("abcdef")

    await session.close()

    assert ex.type is UnauthorizedException


@pytest.mark.asyncio
async def test_get_device_should_return():
    """Test with valid data."""
    with open("tests/api/fixtures/devices/ok.json", encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + DEVICES_URL + "?authToken=abcdef"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        response = await api_client.async_get_devices("abcdef")

    await session.close()

    assert response.master_id == "4tGrXr2CViF8chJEd"
    assert response.master_report_period == 300
    assert response.virtual_device_id == "qVGSJ45vkeqvrHy6g"
    assert response.virtual_battery_id == "ZEdtSVQKto8T53RWa_msb"
