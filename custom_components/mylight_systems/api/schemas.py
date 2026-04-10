"""TypedDict schemas for MyLight Systems API responses."""

from __future__ import annotations

from typing import TypedDict


class MeasureValueSchema(TypedDict):
    """A single measurement value."""

    type: str
    value: float
    unit: str


class MeasureGroupSchema(TypedDict):
    """A group of measurement values."""

    values: list[MeasureValueSchema]


class MeasureTotalContainerSchema(TypedDict):
    """Total measure container."""

    values: list[MeasureValueSchema]


class DeviceSchema(TypedDict):
    """A device entry."""

    id: str
    type: str


class SensorMeasureSchema(TypedDict):
    """A sensor measure nested in a device state."""

    type: str
    value: float
    unit: str


class SensorStateSchema(TypedDict):
    """Sensor state within a device."""

    sensorId: str
    measure: SensorMeasureSchema


class DeviceStateSchema(TypedDict):
    """State of a single device."""

    deviceId: str
    state: str
    sensorStates: list[SensorStateSchema]


class LoginResponseSchema(TypedDict):
    """Login API response."""

    status: str
    authToken: str


class ProfileResponseSchema(TypedDict):
    """Profile API response."""

    status: str
    id: str
    gridType: str


class DevicesResponseSchema(TypedDict):
    """Devices API response."""

    status: str
    devices: list[DeviceSchema]


class MeasuresTotalResponseSchema(TypedDict):
    """Measures total API response."""

    status: str
    measure: MeasureTotalContainerSchema


class MeasuresGroupingResponseSchema(TypedDict):
    """Measures grouping API response."""

    status: str
    measures: list[MeasureGroupSchema]


class StatesResponseSchema(TypedDict):
    """Device states API response."""

    status: str
    deviceStates: list[DeviceStateSchema]


class SwitchResponseSchema(TypedDict):
    """Switch command API response."""

    status: str
    state: str


class RoomDeviceSchema(TypedDict):
    """A device entry within a room."""

    device_id: str
    name: str
    ecnType: str
    type_id: str


class RoomSchema(TypedDict):
    """A room entry."""

    id: str
    name: str
    type: str
    devices: list[RoomDeviceSchema]


class RoomsResponseSchema(TypedDict):
    """Rooms API response."""

    status: str
    rooms: list[RoomSchema]


class ScheduleSchema(TypedDict):
    """A schedule entry."""

    ranges: str
    type: str
    category: str
    enabled: bool


class ScheduleResponseSchema(TypedDict):
    """Schedule API response."""

    status: str
    schedule: ScheduleSchema
