"""DataUpdateCoordinator for mylight_systems."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    MyLightSystemsApiClient,
    MyLightSystemsApiClientAuthenticationError,
    MyLightSystemsApiClientError,
)
from .const import DOMAIN, LOGGER, SCAN_INTERVAL_IN_MINUTES


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class MyLightSystemsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

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
            update_interval=timedelta(minutes=SCAN_INTERVAL_IN_MINUTES),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            result = await self.client.async_get_measures_total()

            if result is None:
                LOGGER.debug("Nothing to retrieve")
                return

            produced_energy: float | None = 0
            grid_energy: float | None = 0

            for value in result["measure"]["values"]:
                if value["type"] == "produced_energy":
                    produced_energy = value["value"]
                if value["type"] == "grid_energy":
                    grid_energy = value["value"]

            return {
                "produced_energy": round(produced_energy / 36e5, 2),
                "grid_energy": round(grid_energy / 36e5, 2),
            }
        except MyLightSystemsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsApiClientError as exception:
            raise UpdateFailed(exception) from exception
