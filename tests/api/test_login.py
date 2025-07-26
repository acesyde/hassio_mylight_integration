"""Unit tests for the login API."""

import json
import os

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from custom_components.mylight_systems.api.client import (
    AUTH_URL,
    DEFAULT_BASE_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import InvalidCredentialsError


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
def undefined_email_response_fixture():
    """Load undefined email response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/undefined_email.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def undefined_password_response_fixture():
    """Load undefined password response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/undefined_password.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def invalid_credentials_response_fixture():
    """Load invalid credentials response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/invalid_credentials.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def valid_login_response_fixture():
    """Load valid login response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/login/ok.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_login__should_raise_invalid_credentials_exception_when_empty_email(
    api_client, undefined_email_response_fixture
):
    """Test with empty email should raise InvalidCredentialsException."""
    # Given
    email = ""
    password = "test"  # noqa: S105
    url = DEFAULT_BASE_URL + AUTH_URL + f"?password={password}"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=undefined_email_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_login(email=email, password=password)

    assert InvalidCredentialsError == exc_info.type


@pytest.mark.asyncio
async def test_login__should_raise_invalid_credentials_exception_when_empty_password(
    api_client, undefined_password_response_fixture
):
    """Test with empty password should raise InvalidCredentialsException."""
    # Given
    email = "test@test.com"
    password = ""
    url = DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=undefined_password_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_login(email=email, password=password)

    assert InvalidCredentialsError == exc_info.type


@pytest.mark.asyncio
async def test_login__should_raise_invalid_credentials_exception_when_wrong_credentials(
    api_client, invalid_credentials_response_fixture
):
    """Test with wrong credentials should raise InvalidCredentialsException."""
    # Given
    email = "test@test.com"
    password = "test"  # noqa: S105
    url = DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com&password=test"

    # When / Then
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=invalid_credentials_response_fixture,
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.async_login(email=email, password=password)

    assert InvalidCredentialsError == exc_info.type


@pytest.mark.asyncio
async def test_login__should_return_auth_token_when_valid_credentials(api_client, valid_login_response_fixture):
    """Test with valid credentials should return auth token."""
    # Given
    email = "test@test.com"
    password = "test"  # noqa: S105
    url = DEFAULT_BASE_URL + AUTH_URL + "?email=test%2540test.com&password=test"

    # When
    with aioresponses() as session_mock:
        session_mock.get(
            url,
            status=200,
            payload=valid_login_response_fixture,
        )

        response = await api_client.async_login(email=email, password=password)

    # Then
    assert "abcdefgh" == response.auth_token
