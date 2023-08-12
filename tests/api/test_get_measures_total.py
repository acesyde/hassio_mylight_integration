"""Unit tests for the get measures total API."""

import json
import os

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    MEASURES_TOTAL_URL,
    MyLightApiClient,
    UnauthorizedException,
)


@pytest.mark.asyncio
async def test_get_measures_total_with_invalid_token_should_throw_exception():
    """Test with valid location data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_total/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = (
        DEFAULT_BASE_URL
        + MEASURES_TOTAL_URL
        + "?authToken=abcdef&measureType=one_phase&deviceId=qVGSJ45vkeqvrHy6g"
    )

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_get_measures_total(
                "abcdef", "one_phase", "qVGSJ45vkeqvrHy6g"
            )

    await session.close()

    assert ex.type is UnauthorizedException


@pytest.mark.asyncio
async def test_get_measures_total_should_return():
    """Test with valid data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/measures_total/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = (
        DEFAULT_BASE_URL
        + MEASURES_TOTAL_URL
        + "?authToken=abcdef&measureType=one_phase&deviceId=qVGSJ45vkeqvrHy6g"
    )

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        response = await api_client.async_get_measures_total(
            "abcdef", "one_phase", "qVGSJ45vkeqvrHy6g"
        )

    await session.close()

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

    assert len(response) == 14
    assert all([a == b.type for a, b in zip(expected_items, response)])
