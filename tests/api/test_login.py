"""Unit tests for the login API."""

import json

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    AUTH_URL,
    InvalidCredentialsException,
    MyLightApiClient,
)


@pytest.mark.asyncio
async def test_login_with_bad_email_should_throw_exception():
    """Test with valid location data."""
    with open(
        "tests/api/fixtures/login/undefined_email.json", encoding="utf-8"
    ) as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = AUTH_URL + "?password=test"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(username="", password="test")

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_with_bad_password_should_throw_exception():
    """Test with valid location data."""
    with open(
        "tests/api/fixtures/login/undefined_password.json", encoding="utf-8"
    ) as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = AUTH_URL + "?email=test%2540test.com"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(username="test@test.com", password="")

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_with_invalid_credentials_should_throw_exception():
    """Test with valid location data."""
    with open(
        "tests/api/fixtures/login/invalid_credentials.json", encoding="utf-8"
    ) as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = AUTH_URL + "?email=test%2540test.com&password=test"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(
                username="test@test.com", password="test"
            )

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_should_return_auth_token():
    """Test with valid location data."""
    with open("tests/api/fixtures/login/ok.json", encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = AUTH_URL + "?email=test%2540test.com&password=test"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(session)

        response = await api_client.async_login(
            username="test@test.com", password="test"
        )

    await session.close()

    assert response.auth_token == "abcdefgh"
