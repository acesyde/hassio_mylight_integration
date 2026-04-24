"""DataUpdateCoordinator for mylight_systems."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import Any, NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
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
    CONF_SCAN_INTERVAL,
    CONF_VIRTUAL_BATTERY_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DEFAULT_SCAN_INTERVAL_IN_MINUTES,
    DOMAIN,
    LOGGER,
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
    water_heater_energy: Measure | None


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator[MyLightSystemsCoordinatorData]):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: MyLightApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.client = client
        self.__auth_token: str | None = None
        self.__token_expiration: datetime | None = None
        self._auth_lock = asyncio.Lock()
        scan_interval = int(config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_IN_MINUTES))
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
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
            if self.__auth_token is None:
                raise UpdateFailed("Authentication token is not set after login")
            auth_token: str = self.__auth_token

            today = date.today().isoformat()
            tomorrow = (date.today() + timedelta(days=1)).isoformat()

            coroutines: list[Any] = [
                self.client.async_get_measures_grouping(
                    auth_token, grid_type, device_id, from_date=today, to_date=tomorrow
                ),
                self.client.async_get_measures_total(auth_token, grid_type, device_id),
                self.client.async_get_battery_state(auth_token, virtual_battery_id),
            ]
            if master_relay_id is not None:
                coroutines.append(self.client.async_get_relay_state(auth_token, master_relay_id))

            results = await asyncio.gather(*coroutines)
            energy_result = results[0]
            total_result = results[1]
            battery_state = results[2]
            master_relay_state = results[3] if master_relay_id is not None else None

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
                water_heater_energy=self.find_measure_by_type(energy_result, "water_heater_energy"),
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
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "auth_failed",
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_failed",
                translation_placeholders={"entry_title": self.config_entry.title},
                data={"entry_id": self.config_entry.entry_id},
            )
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsError as exception:
            raise UpdateFailed(exception) from exception

    def _token_needs_refresh(self) -> bool:
        """Return True if the auth token is missing or expires within 60 seconds."""
        if self.__auth_token is None or self.__token_expiration is None:
            return True
        return self.__token_expiration - timedelta(seconds=60) < datetime.now(UTC)

    async def authenticate_user(self, email, password):
        """Reauthenticate user if needed, serialising refresh with a lock."""
        if not self._token_needs_refresh():
            return
        async with self._auth_lock:
            if not self._token_needs_refresh():
                return
            result = await self.client.async_login(email, password)
            self.__auth_token = result.auth_token
            self.__token_expiration = datetime.now(UTC) + timedelta(hours=2)
            ir.async_delete_issue(self.hass, DOMAIN, "auth_failed")
            LOGGER.info("Authentication successful, token expires at %s", self.__token_expiration.isoformat())

    async def turn_on_master_relay(self):
        """Turn on master relay."""
        if self.__auth_token is None:
            raise UpdateFailed("Authentication token is not set")
        await self.client.async_turn_on(self.__auth_token, self.config_entry.data[CONF_MASTER_RELAY_ID])

    async def turn_off_master_relay(self):
        """Turn off master relay."""
        if self.__auth_token is None:
            raise UpdateFailed("Authentication token is not set")
        await self.client.async_turn_off(self.__auth_token, self.config_entry.data[CONF_MASTER_RELAY_ID])

    @property
    def auth_token(self) -> str | None:
        """Return the current auth token."""
        return self.__auth_token

    def master_relay_is_on(self) -> bool:
        """Return true if master relay is on."""
        if self._data is not None and self._data.master_relay_state is not None:
            return self._data.master_relay_state == "on"
        return False

    @staticmethod
    def find_measure_by_type(measures: list[Measure], name: str) -> Measure | None:
        """Find measure by name."""
        return next((m for m in measures if m.type == name), None)
