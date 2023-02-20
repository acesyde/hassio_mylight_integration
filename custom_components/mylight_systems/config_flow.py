"""Adds config flow for mylight_systems."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol

from .api import (
    MyLightSystemsApiClient,
    MyLightSystemsApiClientAuthenticationError,
    MyLightSystemsApiClientCommunicationError,
    MyLightSystemsApiClientError,
)
from .const import CONF_VIRTUAL_BATTERY_ID, CONF_VIRTUAL_DEVICE_ID, DOMAIN, LOGGER


class MyLightSystemsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                api_client = MyLightSystemsApiClient(
                    username=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                    virtual_device_id=None,
                    virtual_battery_id=None,
                    session=async_create_clientsession(self.hass),
                )

                await api_client.async_login()

                device_ids = await api_client.async_get_device_ids()

                user_input[CONF_VIRTUAL_DEVICE_ID] = device_ids.virtual_device_id
                user_input[CONF_VIRTUAL_BATTERY_ID] = device_ids.virtual_battery_id

                await self.async_set_unique_id(str(user_input[CONF_VIRTUAL_DEVICE_ID]))

                self._abort_if_unique_id_configured()

            except MyLightSystemsApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MyLightSystemsApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MyLightSystemsApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_VIRTUAL_DEVICE_ID],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
                    ),
                }
            ),
            errors=_errors,
        )
