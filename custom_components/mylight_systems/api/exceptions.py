"""Exception handling for MyLight Systems API."""


class MyLightSystemsException(Exception):
    """Exception to indicate a general API error."""

    def __init__(self, msg: str) -> None:
        """Initialize."""
        super().__init__()
        self.__msg = msg

    @property
    def msg(self) -> str:
        """Return error message."""
        return self.__msg


class CommunicationException(MyLightSystemsException):
    """Exception to indicate a communication error."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("A communication error occured")


class InvalidCredentialsException(MyLightSystemsException):
    """Exception to indicate an authentication error."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Invalid credentials")


class UnauthorizedException(MyLightSystemsException):
    """Exception to indicate an authorization error."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__("Unauthorized")
