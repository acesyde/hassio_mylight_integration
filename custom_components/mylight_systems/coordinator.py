"""DataUpdateCoordinator for mylight_systems."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.const import CONF_DEVICE_ID

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
            device_id = self.config_entry.data[CONF_DEVICE_ID]
            return await self.client.async_get_measures_total(device_id)
        except MyLightSystemsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MyLightSystemsApiClientError as exception:
            raise UpdateFailed(exception) from exception
