"""DataUpdateCoordinator for mylight_systems."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import MyLightSystemsApiClient
from .api import MyLightSystemsApiClientAuthenticationError
from .api import MyLightSystemsApiClientError
from .const import DOMAIN
from .const import LOGGER
from .const import SCAN_INTERVAL_IN_MINUTES


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
