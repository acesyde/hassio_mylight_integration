"""Unit tests for the login API."""

import json

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.api import (
    AUTH_URL,
    MyLightApiClient,
)


@pytest.mark.asyncio
async def test_login_with_bad_email_should_throw_exception():
    """Test with valid location data."""
    with open(
        "tests/api/fixtures/login/undefined_email.json", encoding="utf-8"
    ) as file:
        location_data = json.load(file)

        session = aiohttp.ClientSession()

        with aioresponses() as session_mock:
            session_mock.get(
                AUTH_URL,
                payload=location_data,
            )
            accuweather = MyLightApiClient(session)
            await accuweather.async_get_location()

            await session.close()

            assert accuweather.location_name == "Piątek"
            assert accuweather.location_key == "268068"
            assert accuweather.requests_remaining == 23
