"""DataUpdateCoordinator for mylight_systems."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from mylightsystems import (
    MyLightSystemsApiClient,
    MyLightSystemsError,
    MyLightSystemsInvalidAuthError,
    MyLightSystemsUnauthorizedError,
)

from .const import (
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL_IN_MINUTES,
)


class MyLightSystemsCoordinatorData(NamedTuple):
    """Data returned by the coordinator."""

    devices: list = []
    states: dict = {}


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry
    __auth_token: str | None = None
    __token_expiration: datetime | None = None

    def __init__(
        self,
        hass: HomeAssistant,
        client: MyLightSystemsApiClient,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL_IN_MINUTES,
        )

    async def _async_update_data(self) -> MyLightSystemsCoordinatorData:
        """Update data via library."""
        try:
            email = self.config_entry.data[CONF_EMAIL]
            password = self.config_entry.data[CONF_PASSWORD]

            await self.authenticate_user(email, password)

            # Fetch devices from the API
            devices = await self.client.get_devices(self.__auth_token)

            LOGGER.debug("Fetched %d devices from API", len(devices))

            # Fetch states from the API
            states = {}
            try:
                states = await self.client.get_states(self.__auth_token)
                LOGGER.debug("Fetched %d states from API", len(states) if states else 0)
            except Exception as exc:
                LOGGER.warning("Failed to fetch states from API: %s", exc)
                states = {}

            data = MyLightSystemsCoordinatorData(devices=devices, states=states)

            self._data = data

            return data
        except (
            MyLightSystemsUnauthorizedError,
            MyLightSystemsInvalidAuthError,
        ) as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsError as exception:
            raise UpdateFailed(exception) from exception

    async def authenticate_user(self, email, password):
        """Reauthenticate user if needed."""
        if (
            self.__auth_token is None
            or self.__token_expiration is None
            or self.__token_expiration < datetime.now(timezone.utc)
        ):
            result = await self.client.auth(email, password)
            self.__auth_token = result.token
            self.__token_expiration = datetime.now(timezone.utc) + timedelta(hours=2)
