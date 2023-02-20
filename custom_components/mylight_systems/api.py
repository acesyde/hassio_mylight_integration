"""mylight_systems API Client."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import socket

import aiohttp
import async_timeout

from .const import (
    AUTH_PATH,
    BASE_URL,
    DEVICES_PATH,
    LOGGER,
    MEASURES_TOTAL_PATH,
    PROFILE_PATH,
)


class MyLightDevices:
    """MyLight devices ids"""

    virtual_device_id: str | None
    virtual_battery_id: str | None

    def __init__(self, virtual_device_id: str, virtual_battery_id: str):
        self.virtual_device_id = virtual_device_id
        self.virtual_battery_id = virtual_battery_id


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
        virtual_device_id: str,
        virtual_battery_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """MyLight System API Client."""
        self._username = username
        self._password = password
        self._virtual_device_id = virtual_device_id
        self._virtual_battery_id = virtual_battery_id
        self._session = session
        self._token: str | None = None
        self._token_expire_at: datetime | None = None

    async def _should_reauthenticate(self) -> bool:
        """Check login token"""

        LOGGER.debug("Checking Token value: %s and date : %s", self._token, self._token_expire_at)

        return (
            self._token is None
            or self._token_expire_at is None
            or self._token_expire_at < datetime.utcnow()
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
        self._token_expire_at = datetime.utcnow() + timedelta(hours=2)

        LOGGER.debug("Authenticate with token %s for %s", self._token, self._token_expire_at)

    async def async_get_profile(self) -> None:
        """Get user profile from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get user profile")

        await self._api_wrapper(
            method="get",
            url=BASE_URL + PROFILE_PATH,
            params={"authToken": self._token},
        )

    async def async_get_device_ids(self) -> MyLightDevices:
        """Get user profile from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get user devices")

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + DEVICES_PATH,
            params={"authToken": self._token, "adjustmentHistory": "true"},
        )

        device_virtual_id: str | None = self._get_device_id_by_name("virtual", data["devices"])
        device_battery_id: str | None = self._get_device_id_by_name(
            "my_smart_battery", data["devices"]
        )

        LOGGER.debug("Virtual device id : %s", device_virtual_id)
        LOGGER.debug("Virtual battery device id : %s", device_battery_id)

        return MyLightDevices(device_virtual_id, device_battery_id)

    def _get_device_id_by_name(self, name: str, devices: any) -> str | None:
        for device in devices:
            if device["deviceTypeId"] == name:
                return device["id"]
        return None

    async def async_get_measures_total(self) -> any:
        """Get measures total from the MyLight Systems API."""

        await self.async_login()

        LOGGER.debug("Get measures total for device : %s", self._virtual_device_id)

        data = await self._api_wrapper(
            method="get",
            url=BASE_URL + MEASURES_TOTAL_PATH,
            params={
                "authToken": self._token,
                "measureType": "one_phase",
                "deviceId": self._virtual_device_id,
            },
        )

        if data["status"] == "ok":
            return data

        return None

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
            raise MyLightSystemsApiClientError("Something really wrong happened!") from exception
