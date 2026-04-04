"""DataUpdateCoordinator for mylight_systems."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
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
    InvalidCredentialsError,
    MyLightSystemsError,
    UnauthorizedError,
)
from .const import (
    CONF_GRID_TYPE,
    CONF_MASTER_RELAY_ID,
    CONF_VIRTUAL_BATTERY_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL_IN_MINUTES,
)


class MyLightSystemsCoordinatorData(NamedTuple):
    """Data returned by the coordinator."""

    produced_energy: Measure | None
    grid_energy: Measure | None
    grid_energy_without_battery: Measure | None
    autonomy_rate: Measure | None
    self_conso: Measure | None
    msb_charge: Measure | None
    msb_discharge: Measure | None
    green_energy: Measure | None
    battery_state: Measure | None
    master_relay_state: str | None


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator[MyLightSystemsCoordinatorData]):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry
    __auth_token: str | None = None
    __token_expiration: datetime | None = None

    def __init__(
        self,
        hass: HomeAssistant,
        client: MyLightApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_IN_MINUTES),
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> MyLightSystemsCoordinatorData:
        """Update data via library."""
        try:
            email = self.config_entry.data[CONF_EMAIL]
            password = self.config_entry.data[CONF_PASSWORD]
            grid_type = self.config_entry.data[CONF_GRID_TYPE]
            device_id = self.config_entry.data[CONF_VIRTUAL_DEVICE_ID]
            virtual_battery_id = self.config_entry.data[CONF_VIRTUAL_BATTERY_ID]
            master_relay_id = self.config_entry.data.get(CONF_MASTER_RELAY_ID, None)

            await self.authenticate_user(email, password)

            today = date.today().isoformat()
            tomorrow = (date.today() + timedelta(days=1)).isoformat()

            # Energy data from grouping endpoint (daily values)
            energy_result = await self.client.async_get_measures_grouping(
                self.__auth_token, grid_type, device_id, from_date=today, to_date=tomorrow
            )

            # Percentage data from total endpoint (autonomy_rate, self_conso)
            total_result = await self.client.async_get_measures_total(self.__auth_token, grid_type, device_id)

            battery_state = await self.client.async_get_battery_state(self.__auth_token, virtual_battery_id)

            master_relay_state = None
            if master_relay_id is not None:
                master_relay_state = await self.client.async_get_relay_state(self.__auth_token, master_relay_id)

            data = MyLightSystemsCoordinatorData(
                produced_energy=self.find_measure_by_type(energy_result, "produced_energy"),
                grid_energy=self.find_measure_by_type(energy_result, "grid_energy"),
                grid_energy_without_battery=self.find_measure_by_type(energy_result, "grid_sans_msb_energy"),
                autonomy_rate=self.find_measure_by_type(total_result, "autonomy_rate"),
                self_conso=self.find_measure_by_type(total_result, "self_conso"),
                msb_charge=self.find_measure_by_type(energy_result, "msb_charge"),
                msb_discharge=self.find_measure_by_type(energy_result, "msb_discharge"),
                green_energy=self.find_measure_by_type(energy_result, "green_energy"),
                battery_state=battery_state,
                master_relay_state=master_relay_state,
            )

            self._data = data

            LOGGER.info(
                "Coordinator data refreshed: produced=%s, grid=%s, battery=%s, relay=%s",
                data.produced_energy.value if data.produced_energy else None,
                data.grid_energy.value if data.grid_energy else None,
                data.battery_state.value if data.battery_state else None,
                data.master_relay_state,
            )

            return data
        except (
            UnauthorizedError,
            InvalidCredentialsError,
        ) as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsError as exception:
            raise UpdateFailed(exception) from exception

    async def authenticate_user(self, email, password):
        """Reauthenticate user if needed."""
        if self.__auth_token is None or self.__token_expiration is None or self.__token_expiration < datetime.now(UTC):
            result = await self.client.async_login(email, password)
            self.__auth_token = result.auth_token
            self.__token_expiration = datetime.now(UTC) + timedelta(hours=2)
            LOGGER.info("Authentication successful, token expires at %s", self.__token_expiration.isoformat())

    async def turn_on_master_relay(self):
        """Turn on master relay."""
        await self.client.async_turn_on(self.__auth_token, self.config_entry.data[CONF_MASTER_RELAY_ID])

    async def turn_off_master_relay(self):
        """Turn off master relay."""
        await self.client.async_turn_off(self.__auth_token, self.config_entry.data[CONF_MASTER_RELAY_ID])

    def master_relay_is_on(self) -> bool:
        """Return true if master relay is on."""
        if self._data is not None and self._data.master_relay_state is not None:
            return self._data.master_relay_state == "on"
        return False

    @staticmethod
    def find_measure_by_type(measures: list[Measure], name: str) -> Measure | None:
        """Find measure by name."""
        return next((m for m in measures if m.type == name), None)
