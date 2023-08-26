"""Unit tests for the login API."""

import json
import os

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    AUTH_URL,
    DEFAULT_BASE_URL,
    InvalidCredentialsException,
    MyLightApiClient,
)


@pytest.mark.asyncio
async def test_login_with_bad_email_should_throw_exception():
    """Test with valid location data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/undefined_email.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + AUTH_URL + "?password=test"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(email="", password="test")

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_with_bad_password_should_throw_exception():
    """Test with valid location data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/undefined_password.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com"

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(email="test@test.com", password="")

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_with_invalid_credentials_should_throw_exception():
    """Test with valid location data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/invalid_credentials.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = (
        DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com&password=test"
    )

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        with pytest.raises(Exception) as ex:
            await api_client.async_login(
                email="test@test.com", password="test"
            )

    await session.close()

    assert ex.type is InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_should_return_auth_token():
    """Test with valid data."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        response_fixture = json.load(file)

    session = aiohttp.ClientSession()

    url = (
        DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com&password=test"
    )

    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=response_fixture,
        )

        api_client = MyLightApiClient(DEFAULT_BASE_URL, session)

        response = await api_client.async_login(
            email="test@test.com", password="test"
        )

    await session.close()

    assert response.auth_token == "abcdefgh"
