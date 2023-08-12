"""WeatherFlow Data Wrapper."""
from __future__ import annotations

import asyncio
import logging
import socket

import aiohttp
import async_timeout
from yarl import URL

from .const import (
    AUTH_URL,
    DEFAULT_BASE_URL,
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
from .models import InstallationDevices, Login, Measure, UserProfile

_LOGGER = logging.getLogger(__name__)


class MyLightApiClient:
    """Main class to perform MyLight Systems API requests."""

    _session: aiohttp.ClientSession = None

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize."""
        self._session = session
        self._base_url = (
            base_url
            if base_url and not base_url.isspace()
            else DEFAULT_BASE_URL
        )

    async def _execute_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Execute request."""
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT_IN_SECONDS):
                response = await self._session.request(
                    method=method,
                    url=URL(self._base_url).with_path(path),
                    headers=headers,
                    params=params,
                )

                _LOGGER.debug(
                    "Data retrieved from %s, status: %s",
                    response.url,
                    response.status,
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

    async def async_login(self, email: str, password: str) -> Login:
        """Log user and return the authentication token."""
        response = await self._execute_request(
            "get",
            AUTH_URL,
            params={"email": email, "password": password},
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

    async def async_get_devices(self, auth_token: str) -> InstallationDevices:
        """Get user devices (virtual and battery)."""
        response = await self._execute_request(
            "get",
            DEVICES_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        model = InstallationDevices()

        for device in response["devices"]:
            if device["type"] == "vrt":
                model.virtual_device_id = device["id"]
            if device["type"] == "bat":
                model.virtual_battery_id = device["id"]
                model.virtual_battery_capacity = device["batteryCapacity"]
            if device["type"] == "mst":
                model.master_id = device["id"]
                model.master_report_period = device["reportPeriod"]

        return model

    async def async_get_measures_total(
        self, auth_token: str, phase: str, device_id: str
    ) -> list[Measure]:
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

        measures: list[Measure] = []

        for value in response["measure"]["values"]:
            measures.append(
                Measure(value["type"], value["value"], value["unit"])
            )

        return measures

    async def async_get_battery_state(
        self, auth_token: str, battery_id: str
    ) -> Measure | None:
        """Get battery state."""
        response = await self._execute_request(
            "get", STATES_URL, params={"authToken": auth_token}
        )

        if response["status"] == "error":
            if response["error"] == "not.authorized":
                raise UnauthorizedException()

        measure: Measure | None = None

        for device in response["deviceStates"]:
            if device["deviceId"] == battery_id:
                for state in device["sensorStates"]:
                    if state["sensorId"] == battery_id + "-soc":
                        measure = Measure(
                            state["measure"]["type"],
                            state["measure"]["value"],
                            state["measure"]["unit"],
                        )
                        return measure

        return measure
