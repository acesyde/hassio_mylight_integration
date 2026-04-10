"""Api Models."""

from dataclasses import dataclass


@dataclass
class Login:
    """Login model."""

    auth_token: str


@dataclass
class UserProfile:
    """User profile model."""

    subscription_id: str
    grid_type: str


@dataclass
class InstallationDevices:
    """Installation devices representation."""

    master_id: str = ""
    master_report_period: int = 60
    virtual_device_id: str = ""
    virtual_battery_id: str = ""
    master_relay_id: str | None = None

    def __setattr__(self, name: str, value: object) -> None:
        """Default master_report_period to 60 when set to None."""
        if name == "master_report_period" and value is None:
            value = 60
        super().__setattr__(name, value)


@dataclass
class Measure:
    """Represent a measure."""

    type: str
    value: float
    unit: str


@dataclass
class RoomDevice:
    """A device within a room."""

    device_id: str
    name: str
    ecn_type: str
    type_id: str


@dataclass
class Room:
    """A room containing devices."""

    id: str
    name: str
    type: str
    devices: list[RoomDevice]


@dataclass
class Schedule:
    """A schedule (e.g. electric tariff)."""

    ranges: str
    type: str
    category: str
    enabled: bool
