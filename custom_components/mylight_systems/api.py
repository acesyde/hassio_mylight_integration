"""mylight_systems API Client."""
from __future__ import annotations

import asyncio
import socket
from datetime import datetime
from datetime import timedelta

import aiohttp
import async_timeout

from .const import AUTH_PATH
from .const import BASE_URL
from .const import DEVICES_PATH
from .const import LOGGER
from .const import MEASURES_TOTAL_PATH
from .const import PROFILE_PATH


class MyLightSystemsApiClientError(Exception):
    """Exception to indicate a general API error."""


class MyLightSystemsApiClientCommunicationError(MyLightSystemsApiClientError):
    """Exception to indicate a communication error."""


class MyLightSystemsApiClientAuthenticationError(MyLightSystemsApiClientError):
    """Exception to indicate an authentication error."""


class MyLightSystemsApiClient:
    """Sample API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """MyLight System API Client."""
        self._username = username
        self._password = password
        self._session = session
        self._token = ""
        self._last_token_date: datetime | None = None

    async def _should_reauthenticate(self) -> bool:
        """Check login token"""
        LOGGER.debug("Checking Token value: %s", self._token)

        return (
            self._token == ""
            or self._last_token_date is None
            or self._last_token_date < datetime.utcnow() + timedelta(hours=1)
        )

    async def async_login(self) -> None:
        """Login from the MyLight Systems API."""

        if await self._should_reauthenticate() is False:
            return

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + AUTH_PATH,
            params={"email": self._username, "password": self._password},
        )

        if data["status"] == "error" and data["error"] in (
            "invalid.credentials",
            "not.authorized",
        ):
            raise MyLightSystemsApiClientAuthenticationError(
                "Invalid credentials",
            )

        self._token = data["authToken"]
        self._last_token_date = datetime.utcnow()

    async def async_get_profile(self) -> None:
        """Get user profile from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get user profile")

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + PROFILE_PATH,
            params={"authToken": self._token},
        )

    async def async_get_devices(self) -> None:
        """Get user profile from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get user devices")

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + DEVICES_PATH,
            params={"authToken": self._token, "adjustmentHistory": "true"},
        )

    async def async_get_measures_total(self, device_id: str) -> any:
        """Get measures total from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get measures total for device : %s", device_id)

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + MEASURES_TOTAL_PATH,
            params={
                "authToken": self._token,
                "measureType": "one_phase",
                "deviceId": device_id,
            },
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )

                LOGGER.debug("Retrieved data from API: %s", response.request_info.url)

                response.raise_for_status()
                data = await response.json()

                LOGGER.debug("Retrieved data from API: %s", data)

                return data

        except (
            asyncio.TimeoutError,
            aiohttp.ClientError,
            socket.gaierror,
        ) as exception:
            LOGGER.debug("An error occured : %s", exception, exc_info=True)
            raise MyLightSystemsApiClientCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            LOGGER.debug("An error occured : %s", exception, exc_info=True)
            raise MyLightSystemsApiClientError(
                "Something really wrong happened!"
            ) from exception
