"""DataUpdateCoordinator for mylight_systems."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from custom_components.mylight_systems.api.models import Measure

from .api.client import MyLightApiClient
from .api.exceptions import (
    InvalidCredentialsException,
    MyLightSystemsException,
    UnauthorizedException,
)
from .const import (
    CONF_GRID_TYPE,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL_IN_MINUTES,
)


class MyLightSystemsCoordinatorData:
    """Data returned by the coordinator."""

    def __init__(
        self,
        produced_energy: Measure,
        grid_energy: Measure,
        grid_energy_without_battery: Measure,
        autonomy_rate: Measure,
        self_conso: Measure,
    ) -> None:
        """Initialize."""
        self._produced_energy = produced_energy
        self._grid_energy = grid_energy
        self._autonomy_rate = autonomy_rate
        self._self_conso = self_conso


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: MyLightApiClient,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_IN_MINUTES),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            email = self.self.config_entry.data[CONF_EMAIL]
            password = self.self.config_entry.data[CONF_PASSWORD]
            grid_type = self.self.config_entry.data[CONF_GRID_TYPE]
            device_id = self.self.config_entry.data[CONF_VIRTUAL_DEVICE_ID]

            await self.authenticate_user(email, password)

            result = await self.client.async_get_measures_total(
                self.__auth_token, grid_type, device_id
            )

            return MyLightSystemsCoordinatorData(
                result["produced_energy"],
                result["grid_energy"],
                result["grid_sans_msb_energy"],
                result["autonomy_rate"],
                result["self_conso"],
            )
        except (
            UnauthorizedException,
            InvalidCredentialsException,
        ) as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsException as exception:
            raise UpdateFailed(exception) from exception

    async def authenticate_user(self, email, password):
        """Reauthenticate user if needed."""
        if (
            self.__auth_token is None
            or self.__token_expiration is None
            or self.__token_expiration < datetime.utcnow()
        ):
            result = await self.client.async_login(email, password)
            self.__auth_token = result.__auth_token
            self.__token_expiration = datetime.utcnow() + timedelta(hours=2)
