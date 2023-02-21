"""WeatherFlow Data Wrapper."""
from __future__ import annotations

import asyncio
import logging
import socket

import aiohttp
import async_timeout

from .models import UserProfile, Login

from .const import (
    AUTH_URL,
    DEFAULT_TIMEOUT_IN_SECONDS,
    DEVICES_URL,
    MEASURES_TOTAL_URL,
    PROFILE_URL,
    STATES_URL,
)
from .exceptions import (
    CommunicationException,
    InvalidCredentialsException,
    UnauthorizedException,
)

_LOGGER = logging.getLogger(__name__)


class MyLightApiClient:
    """Main class to perform MyLight Systems API requests."""

    _session: aiohttp.ClientSession = None

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize."""
        self._session = session

    async def _execute_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Execute request."""
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT_IN_SECONDS):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                )

                _LOGGER.debug(
                    "Data retrieved from %s, status: %s", url, response.status
                )
                response.raise_for_status()
                data = await response.json()

                return data
        except (
            asyncio.TimeoutError,
            aiohttp.ClientError,
            socket.gaierror,
            Exception,
        ) as exception:
            _LOGGER.debug("An error occured : %s", exception, exc_info=True)
            raise CommunicationException() from exception

    async def async_login(self, username: str, password: str) -> Login:
        """Log user and return the authentication token."""
        response = await self._execute_request(
            "get",
            AUTH_URL,
            params={"email": username, "password": password},
        )

        if response["status"] == "error":
            if response["error"] in (
                "invalid.credentials",
                "undefined.email",
                "undefined.password",
            ):
                raise InvalidCredentialsException()

        return Login(response["authToken"])

    async def async_get_profile(self, auth_token: str) -> UserProfile:
        """Get user profile."""
        response = await self._execute_request(
            "get",
            PROFILE_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        grid_type: str = "one_phase"
        if response["gridType"] == "1 phase":
            grid_type = "one_phase"
        else:
            grid_type = "three_phases"

        return UserProfile(response["id"], grid_type)

    async def async_get_devices(
        self, auth_token: str
    ) -> dict[str, any] | None:
        """Get user devices (virtual and battery)."""
        response = await self._execute_request(
            "get",
            DEVICES_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        device_virtual_id: str | None = None
        device_battery_id: str | None = None

        for device in response["devices"]:
            if device["deviceTypeId"] == "virtual":
                device_virtual_id = device["id"]
            if device["deviceTypeId"] == "my_smart_battery":
                device_battery_id = device["id"]

        if device_virtual_id is None and device_battery_id is None:
            return None

        return {device_virtual_id, device_battery_id}

    async def async_get_state(
        self, auth_token: str, devices_id: list(str)
    ) -> dict[str, dict[str, any]] | None:
        """Get devices states."""
        response = await self._execute_request(
            "get",
            STATES_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        states: dict[str, dict[str, object]] = []

        for device_id in devices_id:
            for device_state in response["deviceStates"]:
                if (
                    device_state["deviceId"] == device_id
                    and device_state["state"] == "on"
                ):
                    for sensor_state in device_state["sensorStates"]:
                        states[device_id][sensor_state["type"]] = {
                            "value": sensor_state["value"],
                            "unit": sensor_state["unit"],
                            "date": sensor_state["date"],
                        }

        if len(states) <= 0:
            return None

        return states

    async def async_get_measures_total(
        self, auth_token: str, phase: str, device_id: str
    ) -> dict[str, object] | None:
        """Get device measures total."""
        response = await self._execute_request(
            "get",
            MEASURES_TOTAL_URL,
            params={
                "authToken": auth_token,
                "measureType": phase,
                "deviceId": device_id,
            },
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        result: dict[str, any] | None = None

        for value in response["measure"]["values"]:
            if value["unit"] == "Ws":
                result[value["type"]] = {
                    self._convert_in_watt(value["value"]),
                    value["unit"],
                }
            else:
                result[value["type"]] = {value["value"]}

        return result

    def _convert_in_watt(number: float) -> float:
        return round(number / 300, 2)
