"""mylight_systems API Client."""
from __future__ import annotations

import asyncio
import socket

import aiohttp
import async_timeout
from datetime import date, datetime, timedelta
from .const import BASE_URL, AUTH_PATH, LOGGER, MEASURES_TOTAL_PATH


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
        self._last_token_date: date | None = None

    async def check_token(self) -> any:
        """Check login token"""
        LOGGER.debug("Checking Token value: %s", self._token)
        if (
            self._token == ""
            or self._last_token_date is None
            or self._last_token_date < datetime.utcnow() + timedelta(hours=1)
        ):
            login_result = await self.async_login()
            self._token = login_result["authToken"]

    async def async_login(self) -> any:
        """Login from the MyLight Systems API"""
        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + AUTH_PATH,
            params={"email": self._username, "password": self._password},
        )

        if data["status"] == "error" and data["error"] in (
            "invalid.credentials",
            "not.authorized",
        ):
            LOGGER.warning("Unable to retrieve credentials")
            raise MyLightSystemsApiClientAuthenticationError(
                "Invalid credentials",
            )

        return data

    async def async_get_measures_total(self, device_id: str) -> any:
        """Get measures total from the API."""

        await self.check_token()

        return await self._api_wrapper(
            method="get",
            url=BASE_URL + MEASURES_TOTAL_PATH,
            params={
                "authToken": self._token,
                "measureType": "one_phase",
                "device_id": device_id,
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
                response.raise_for_status()
                data = await response.json()

                LOGGER.debug("Retrieved data from API: %s", data)

                return data

        except asyncio.TimeoutError as exception:
            raise MyLightSystemsApiClientCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise MyLightSystemsApiClientCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise MyLightSystemsApiClientError(
                "Something really wrong happened!"
            ) from exception
