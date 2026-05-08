"""Custom integration to integrate mylight_systems with Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import DEFAULT_BASE_URL, MyLightApiClient
from .const import (
    CONF_GMD_DEVICES,
    CONF_MASTER_RELAY_ID,
    CONF_RELAY_DEVICES,
    LOGGER,
    PLATFORMS,
)
from .coordinator import MyLightSystemsDataUpdateCoordinator
from .services import async_setup_services, async_unload_services

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

    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Handle removal of an entry."""
    await async_unload_services(hass)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: MyLightConfigEntry) -> bool:
    """Migrate old entry data to the current version."""
    LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version > 2:
        return False

    if entry.version == 1:
        new_data = {**entry.data}
        old_relay_id = new_data.pop(CONF_MASTER_RELAY_ID, None)
        new_data[CONF_RELAY_DEVICES] = (
            [{"id": old_relay_id, "name": "", "device_type_id": None, "type_override": None}] if old_relay_id else []
        )
        new_data[CONF_GMD_DEVICES] = []
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
        LOGGER.debug("Migration to version 2 successful")
        return True

    return True
