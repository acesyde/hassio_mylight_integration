"""MyLight Systems API client."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any

import aiohttp
import async_timeout
from yarl import URL

from .const import (
    AUTH_URL,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_IN_SECONDS,
    DEVICES_URL,
    ERR_INVALID_CREDENTIALS,
    ERR_NOT_AUTHORIZED,
    ERR_SWITCH_NOT_ALLOWED,
    ERR_UNDEFINED_EMAIL,
    ERR_UNDEFINED_PASSWORD,
    MEASURES_GROUPING_URL,
    MEASURES_TOTAL_URL,
    PROFILE_URL,
    STATES_URL,
    SWITCH_URL,
)
from .exceptions import (
    CommunicationError,
    InvalidCredentialsError,
    MyLightSystemsError,
    UnauthorizedError,
)
from .models import InstallationDevices, Login, Measure, UserProfile

_LOGGER = logging.getLogger(__name__)


class MyLightApiClient:
    """Main class to perform MyLight Systems API requests."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize."""
        self._session: aiohttp.ClientSession = session
        self._base_url = base_url if base_url and not base_url.isspace() else DEFAULT_BASE_URL

    async def _execute_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
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
        ) as exception:
            _LOGGER.debug("An error occured : %s", exception, exc_info=True)
            raise CommunicationError() from exception

    async def async_login(self, email: str, password: str) -> Login:
        """Log user and return the authentication token."""
        response = await self._execute_request(
            "get",
            AUTH_URL,
            params={"email": email, "password": password},
        )

        if response["status"] == "error":
            if response["error"] in (
                ERR_INVALID_CREDENTIALS,
                ERR_UNDEFINED_EMAIL,
                ERR_UNDEFINED_PASSWORD,
            ):
                raise InvalidCredentialsError()
            raise MyLightSystemsError(response.get("error", "unknown error"))

        return Login(response["authToken"])

    async def async_get_profile(self, auth_token: str) -> UserProfile:
        """Get user profile."""
        response = await self._execute_request(
            "get",
            PROFILE_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        match response["gridType"]:
            case "1 phase":
                grid_type = "one_phase"
            case "3 phases":
                grid_type = "three_phases"
            case _:
                grid_type = "one_phase"

        return UserProfile(response["id"], grid_type)

    async def async_get_devices(self, auth_token: str) -> InstallationDevices:
        """Get user devices (virtual and battery)."""
        response = await self._execute_request(
            "get",
            DEVICES_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        model = InstallationDevices()

        try:
            devices = response["devices"]
        except KeyError as err:
            raise MyLightSystemsError("Missing 'devices' key in response") from err

        for device in devices:
            if device["type"] == "vrt":
                model.virtual_device_id = device["id"]
            if device["type"] == "bat":
                model.virtual_battery_id = device["id"]
            if device["type"] == "mst":
                model.master_id = device["id"]
                model.master_report_period = device["reportPeriod"]
            if device["type"] == "sw":
                model.master_relay_id = device["id"]

        return model

    async def async_get_measures_total(self, auth_token: str, phase: str, device_id: str) -> list[Measure]:
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
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        measures: list[Measure] = []

        try:
            values = response["measure"]["values"]
        except KeyError as err:
            raise MyLightSystemsError("Missing 'measure' key in response") from err

        for value in values:
            measures.append(Measure(value["type"], value["value"], value["unit"]))

        return measures

    async def async_get_measures_grouping(
        self,
        auth_token: str,
        phase: str,
        device_id: str,
        from_date: str,
        to_date: str,
        group_type: str = "day",
    ) -> list[Measure]:
        """Get device measures using the grouping endpoint."""
        response = await self._execute_request(
            "get",
            MEASURES_GROUPING_URL,
            params={
                "authToken": auth_token,
                "groupType": group_type,
                "fromDate": from_date,
                "toDate": to_date,
                "measureType": phase,
                "deviceId": device_id,
            },
        )

        if response["status"] == "error":
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        measures: list[Measure] = []

        try:
            measure_groups = response["measures"]
        except KeyError as err:
            raise MyLightSystemsError("Missing 'measures' key in response") from err

        if measure_groups:
            for value in measure_groups[0]["values"]:
                measures.append(Measure(value["type"], value["value"], value["unit"]))

        return measures

    async def async_get_battery_state(self, auth_token: str, battery_id: str) -> Measure | None:
        """Get battery state."""
        response = await self._execute_request("get", STATES_URL, params={"authToken": auth_token})

        if response["status"] == "error":
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

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

    async def async_turn_off(self, auth_token: str, relay_id: str) -> str:
        """Turn off the switch."""
        response = await self._execute_request(
            "get",
            SWITCH_URL,
            params={
                "authToken": auth_token,
                "id": relay_id,
                "on": "false",
            },
        )

        if response["status"] == "error":
            if response["error"] == ERR_SWITCH_NOT_ALLOWED:
                return "off"
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        return response["state"]

    async def async_turn_on(self, auth_token: str, relay_id: str) -> str:
        """Turn on the switch."""
        response = await self._execute_request(
            "get",
            SWITCH_URL,
            params={
                "authToken": auth_token,
                "id": relay_id,
                "on": "true",
            },
        )

        if response["status"] == "error":
            if response["error"] == ERR_SWITCH_NOT_ALLOWED:
                return "on"
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        return response["state"]

    async def async_get_relay_state(self, auth_token: str, relay_id: str) -> str | None:
        """Get relay state."""
        response = await self._execute_request("get", STATES_URL, params={"authToken": auth_token})

        if response["status"] == "error":
            if response["error"] == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        for device in response["deviceStates"]:
            if device["deviceId"] == relay_id:
                return device["state"]

        return None
