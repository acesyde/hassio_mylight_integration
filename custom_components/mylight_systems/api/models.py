"""Api Models."""


class Login:
    """Login model."""

    __auth_token: str = None

    def __init__(self, auth_token: str) -> None:
        """Initialize."""
        self.__auth_token = auth_token

    @property
    def auth_token(self):
        """Return auth_token."""
        return self.__auth_token


class UserProfile:
    """User profile model."""

    __subscription_id: str = None
    __grid_type: str = None

    def __init__(self, subscription_id: str, grid_type: str) -> None:
        """Initialize."""
        self.__subscription_id = subscription_id
        self.__grid_type = grid_type

    @property
    def subscription_id(self):
        """Return subscription id."""
        return self.__subscription_id

    @property
    def grid_type(self):
        """Return grid type."""
        return self.__grid_type


class InstallationDevices:
    """Installation devices representation."""

    __master_id: str = None
    __master_report_period: int = 60
    __virtual_device_id: str = None
    __virtual_battery_id: str = None
    __master_relay_id: str = None

    @property
    def master_id(self):
        """Return master id."""
        return self.__master_id

    @master_id.setter
    def master_id(self, value: str):
        """Set master id."""
        self.__master_id = value

    @property
    def master_report_period(self):
        """Return master report period."""
        return self.__master_report_period

    @master_report_period.setter
    def master_report_period(self, value: int):
        """Set master report period."""
        if value is None:
            self.__master_report_period = 60
        self.__master_report_period = value

    @property
    def virtual_device_id(self):
        """Return virtual device id."""
        return self.__virtual_device_id

    @virtual_device_id.setter
    def virtual_device_id(self, value: str):
        """Set virtual device id id."""
        self.__virtual_device_id = value

    @property
    def virtual_battery_id(self):
        """Return virtual battery id."""
        return self.__virtual_battery_id

    @virtual_battery_id.setter
    def virtual_battery_id(self, value: str):
        """Set virtual battery id."""
        self.__virtual_battery_id = value

    @property
    def master_relay_id(self):
        """Return master relay id."""
        return self.__master_relay_id

    @master_relay_id.setter
    def master_relay_id(self, value: str):
        """Set master relay id."""
        self.__master_relay_id = value


class Measure:
    """Represent a measure."""

    def __init__(self, key: str, value: float, unit: str) -> None:
        """Initialize."""
        self.__type = key
        self.__value = value
        self.__unit = unit

    @property
    def type(self) -> str:
        """Return measure type."""
        return self.__type

    @property
    def value(self) -> float:
        """Return measure value."""
        return self.__value

    @property
    def unit(self) -> str:
        """Return measure unit."""
        return self.__unit
