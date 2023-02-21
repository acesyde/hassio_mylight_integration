"""DataUpdateCoordinator for mylight_systems."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import NamedTuple

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


class MyLightSystemsCoordinatorData(NamedTuple):
    """Data returned by the coordinator."""

    produced_energy: Measure
    grid_energy: Measure
    grid_energy_without_battery: Measure
    autonomy_rate: Measure
    self_conso: Measure


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry
    __auth_token: str | None = None
    __token_expiration: datetime | None = None

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

    async def _async_update_data(self) -> MyLightSystemsCoordinatorData:
        """Update data via library."""
        try:
            email = self.config_entry.data[CONF_EMAIL]
            password = self.config_entry.data[CONF_PASSWORD]
            grid_type = self.config_entry.data[CONF_GRID_TYPE]
            device_id = self.config_entry.data[CONF_VIRTUAL_DEVICE_ID]

            await self.authenticate_user(email, password)

            result = await self.client.async_get_measures_total(
                self.__auth_token, grid_type, device_id
            )

            return MyLightSystemsCoordinatorData(
                produced_energy=self.find_measure_by_type(
                    result, "produced_energy"
                ),
                grid_energy=self.find_measure_by_type(result, "grid_energy"),
                grid_energy_without_battery=self.find_measure_by_type(
                    result, "grid_sans_msb_energy"
                ),
                autonomy_rate=self.find_measure_by_type(
                    result, "autonomy_rate"
                ),
                self_conso=self.find_measure_by_type(result, "self_conso"),
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
            self.__auth_token = result.auth_token
            self.__token_expiration = datetime.utcnow() + timedelta(hours=2)

    def find_measure_by_type(
        self, measures: list[Measure], name: str
    ) -> Measure:
        """Find measure by name."""
        return next(m for m in measures if m.type == name)
