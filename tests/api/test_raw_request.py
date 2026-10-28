"""Unit tests for the raw request API method."""

import asyncio
import json
import os

import aiohttp
import pytest
import pytest_asyncio

from custom_components.mylight_systems.api import client
from custom_components.mylight_systems.api.client import (
    DEFAULT_BASE_URL,
    PROFILE_URL,
    MyLightApiClient,
)
from custom_components.mylight_systems.api.exceptions import CommunicationError

from . import mock_get


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
def valid_profile_fixture():
    """Load valid profile response fixture."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.normcase(dir_path + "/fixtures/profile/ok_one_phase.json")
    with open(fixture_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.asyncio
async def test_async_raw_request__should_return_unmodified_json(api_client, aresponses, valid_profile_fixture):
    """Test that async_raw_request returns the raw JSON dict unchanged."""
    # Given
    token = "abcdef"  # noqa: S105
    url = DEFAULT_BASE_URL + PROFILE_URL + f"?authToken={token}"

    # When
    mock_get(aresponses, url, valid_profile_fixture)
    result = await api_client.async_raw_request("get", PROFILE_URL, params={"authToken": token})

    # Then
    assert result == valid_profile_fixture


# shortcut: aresponses 3.0.0 calls asyncio.iscoroutinefunction for callable handlers, drop once it is fixed upstream
@pytest.mark.filterwarnings("ignore:.*asyncio.iscoroutinefunction.*:DeprecationWarning")
@pytest.mark.asyncio
async def test_async_raw_request__should_raise_communication_error_on_timeout(api_client, aresponses, monkeypatch):
    """Test that async_raw_request raises CommunicationError on network failure."""
    # Given
    token = "abcdef"  # noqa: S105
    monkeypatch.setattr(client, "DEFAULT_TIMEOUT_IN_SECONDS", 0.05)

    async def slow(_request):
        await asyncio.sleep(1)

    # When / Then
    aresponses.add(
        "myhome.mylight-systems.com", f"{PROFILE_URL}?authToken={token}", "get", slow, match_querystring=True
    )

    with pytest.raises(CommunicationError):
        await api_client.async_raw_request("get", PROFILE_URL, params={"authToken": token})
