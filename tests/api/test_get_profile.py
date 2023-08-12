"""Unit tests for the get profile API."""
import json
import os

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    PROFILE_URL,
    MyLightApiClient,
    UnauthorizedException,
)


@pytest.mark.asyncio
async def test_get_profile_with_invalid_token_should_throw_exception():
    """Test with valid location data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/profile/unauthorized.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + PROFILE_URL + "?authToken=abcdef"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_get_profile("abcdef")

    await session.close()

    assert ex.type is UnauthorizedException


@pytest.mark.asyncio
async def test_get_profile_with_one_phase_grid_type_should_return():
    """Test with valid data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/profile/ok_one_phase.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + PROFILE_URL + "?authToken=abcdef"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        response = await api_client.async_get_profile("abcdef")

    await session.close()

    assert response.subscription_id == "40oXYqq6nM7R9zGK"
    assert response.grid_type == "one_phase"
