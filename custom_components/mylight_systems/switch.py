from dataclasses import dataclass
from typing import Callable, Coroutine, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .api.exceptions import MyLightSystemsException
from .const import LOGGER, DATA_COORDINATOR, CONF_MASTER_RELAY_ID
from .coordinator import MyLightSystemsDataUpdateCoordinator
from .entity import IntegrationMyLightSystemsEntity


@dataclass(kw_only=True)
class MyLightSystemsSwitchEntityDescription(SwitchEntityDescription):
    """Describes MyLight Systems switch entity."""

    is_on_fn: Callable[[MyLightSystemsDataUpdateCoordinator], bool]
    turn_on_fn: Callable[[MyLightSystemsDataUpdateCoordinator], Callable[[], Coroutine[Any, Any, None]]]
    turn_off_fn: Callable[[MyLightSystemsDataUpdateCoordinator], Callable[[], Coroutine[Any, Any, None]]]


master_relay_switch = MyLightSystemsSwitchEntityDescription(
    key="master_relay",
    name="Master relay",
    icon="mdi:light-switch",
    is_on_fn=lambda coordinator: coordinator.master_relay_is_on,
    turn_on_fn=lambda coordinator: coordinator.turn_on_master_relay,
    turn_off_fn=lambda coordinator: coordinator.turn_off_master_relay,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Configure switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    switches: list[MyLightSystemsSwitchEntityDescription] = []

    if entry.data[CONF_MASTER_RELAY_ID] is not None:
        switches.append(master_relay_switch)

    async_add_entities(
        [MyLightSystemsSwitch(entry.entry_id, coordinator, description) for description in switches],
        True,
    )


class MyLightSystemsSwitch(IntegrationMyLightSystemsEntity, SwitchEntity):
    """Defines a MyLight Systems switch."""

    def __init__(
        self,
        entry_id: ConfigEntry,
        coordinator: MyLightSystemsDataUpdateCoordinator,
        entity_description: MyLightSystemsSwitchEntityDescription,
    ) -> None:
        """Initialize MyLight Systems switch."""
        super().__init__(coordinator)
        self.entity_id = f"{DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self.entity_description = entity_description

    @property
    def is_on(self):
        """Return true if it is on."""
        return self.entity_description.is_on_fn(self.coordinator)()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.entity_description.turn_off_fn(self.coordinator)()
            await self.coordinator.async_request_refresh()
        except MyLightSystemsException:
            LOGGER.error("An error occurred while turning off MyLight Systems switch")
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.entity_description.turn_on_fn(self.coordinator)()
            await self.coordinator.async_request_refresh()
        except MyLightSystemsException:
            LOGGER.error("An error occurred while turning on MyLight Systems switch")
            self._attr_available = False
