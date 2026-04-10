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
    ROOMS_URL,
    SCHEDULE_URL,
    STATES_URL,
    SWITCH_URL,
)
from .exceptions import (
    CommunicationError,
    InvalidCredentialsError,
    MyLightSystemsError,
    UnauthorizedError,
)
from .models import InstallationDevices, Login, Measure, Room, RoomDevice, Schedule, UserProfile
from .schemas import (
    DevicesResponseSchema,
    LoginResponseSchema,
    MeasuresGroupingResponseSchema,
    MeasuresTotalResponseSchema,
    ProfileResponseSchema,
    RoomsResponseSchema,
    ScheduleResponseSchema,
    StatesResponseSchema,
    SwitchResponseSchema,
)

_LOGGER = logging.getLogger(__name__)


def _validate_response(response: dict[str, Any], *required_keys: str) -> None:
    """Raise MyLightSystemsError if any required key is absent from the API response."""
    for key in required_keys:
        if key not in response:
            raise MyLightSystemsError(f"Unexpected API response: missing field '{key}'")


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
        response: LoginResponseSchema = await self._execute_request(
            "get",
            AUTH_URL,
            params={"email": email, "password": password},
        )

        if response["status"] == "error":
            if response.get("error") in (
                ERR_INVALID_CREDENTIALS,
                ERR_UNDEFINED_EMAIL,
                ERR_UNDEFINED_PASSWORD,
            ):
                raise InvalidCredentialsError()
            raise MyLightSystemsError(response.get("error", "unknown error"))

        _validate_response(response, "authToken")
        return Login(response["authToken"])

    async def async_get_profile(self, auth_token: str) -> UserProfile:
        """Get user profile."""
        response: ProfileResponseSchema = await self._execute_request(
            "get",
            PROFILE_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "id", "gridType")
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
        response: DevicesResponseSchema = await self._execute_request(
            "get",
            DEVICES_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "devices")
        model = InstallationDevices()
        devices = response["devices"]

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
        response: MeasuresTotalResponseSchema = await self._execute_request(
            "get",
            MEASURES_TOTAL_URL,
            params={
                "authToken": auth_token,
                "measureType": phase,
                "deviceId": device_id,
            },
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "measure")
        measures: list[Measure] = []
        values = response["measure"]["values"]

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
        response: MeasuresGroupingResponseSchema = await self._execute_request(
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
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "measures")
        measures: list[Measure] = []
        measure_groups = response["measures"]

        if measure_groups:
            for value in measure_groups[0]["values"]:
                measures.append(Measure(value["type"], value["value"], value["unit"]))

        return measures

    async def async_get_battery_state(self, auth_token: str, battery_id: str) -> Measure | None:
        """Get battery state."""
        response: StatesResponseSchema = await self._execute_request(
            "get", STATES_URL, params={"authToken": auth_token}
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "deviceStates")
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
        response: SwitchResponseSchema = await self._execute_request(
            "get",
            SWITCH_URL,
            params={
                "authToken": auth_token,
                "id": relay_id,
                "on": "false",
            },
        )

        if response["status"] == "error":
            if response.get("error") == ERR_SWITCH_NOT_ALLOWED:
                return "off"
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "state")
        return response["state"]

    async def async_turn_on(self, auth_token: str, relay_id: str) -> str:
        """Turn on the switch."""
        response: SwitchResponseSchema = await self._execute_request(
            "get",
            SWITCH_URL,
            params={
                "authToken": auth_token,
                "id": relay_id,
                "on": "true",
            },
        )

        if response["status"] == "error":
            if response.get("error") == ERR_SWITCH_NOT_ALLOWED:
                return "on"
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "state")
        return response["state"]

    async def async_get_relay_state(self, auth_token: str, relay_id: str) -> str | None:
        """Get relay state."""
        response: StatesResponseSchema = await self._execute_request(
            "get", STATES_URL, params={"authToken": auth_token}
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "deviceStates")
        for device in response["deviceStates"]:
            if device["deviceId"] == relay_id:
                return device["state"]

        return None

    async def async_get_rooms(self, auth_token: str) -> list[Room]:
        """Get rooms with their devices."""
        response: RoomsResponseSchema = await self._execute_request(
            "get",
            ROOMS_URL,
            params={"authToken": auth_token},
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "rooms")
        rooms: list[Room] = []

        for room_data in response["rooms"]:
            devices = [
                RoomDevice(
                    device_id=d["device_id"],
                    name=d["name"],
                    ecn_type=d["ecnType"],
                    type_id=d["type_id"],
                )
                for d in room_data["devices"]
            ]
            rooms.append(Room(room_data["id"], room_data["name"], room_data["type"], devices))

        return rooms

    async def async_get_schedule(self, auth_token: str, schedule_type: str) -> Schedule:
        """Get schedule by type."""
        response: ScheduleResponseSchema = await self._execute_request(
            "get",
            SCHEDULE_URL,
            params={"authToken": auth_token, "scheduleType": schedule_type},
        )

        if response["status"] == "error":
            if response.get("error") == ERR_NOT_AUTHORIZED:
                raise UnauthorizedError()

        _validate_response(response, "schedule")
        schedule_data = response["schedule"]

        return Schedule(
            ranges=schedule_data["ranges"],
            type=schedule_data["type"],
            category=schedule_data["category"],
            enabled=schedule_data["enabled"],
        )
