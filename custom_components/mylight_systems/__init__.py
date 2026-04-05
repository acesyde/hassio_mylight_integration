"""Custom integration to integrate mylight_systems with Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import DEFAULT_BASE_URL, MyLightApiClient
from .const import LOGGER, PLATFORMS
from .coordinator import MyLightSystemsDataUpdateCoordinator

type MyLightConfigEntry = ConfigEntry[MyLightSystemsDataUpdateCoordinator]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Set up this integration using UI."""
    session = async_get_clientsession(hass)

    client = MyLightApiClient(
        base_url=entry.data.get(CONF_URL, DEFAULT_BASE_URL),
        session=session,
    )
    coordinator = MyLightSystemsDataUpdateCoordinator(hass=hass, client=client, config_entry=entry)

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        entry.add_update_listener(lambda hass, entry: hass.config_entries.async_reload(entry.entry_id))
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Migrate old entry data to the current version."""
    LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        LOGGER.debug("Migration to version %s successful", entry.version)
        return True

    LOGGER.error(
        "Cannot migrate config entry from version %s: unknown version. Please remove and re-add the integration.",
        entry.version,
    )
    return False
