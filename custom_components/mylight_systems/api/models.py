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

    __id: str = None
    __grid_type: str = None

    def __init__(self, id: str, grid_type: str) -> None:
        """Initialize."""
        self.__id = id
        self.__grid_type = grid_type

    @property
    def id(self):
        """Return subscription id."""
        return self.__id

    @property
    def grid_type(self):
        """Return grid type."""
        return self.__grid_type
