"""Adds config flow for mylight_systems."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from mylightsystems import MyLightSystemsApiClient
from mylightsystems.const import DEFAULT_BASE_URL
from mylightsystems.exceptions import MyLightSystemsConnectionError, MyLightSystemsError, MyLightSystemsInvalidAuthError

from .const import (
    CONF_GRID_TYPE,
    CONF_SUBSCRIPTION_ID,
    DOMAIN,
    LOGGER,
)


class MyLightSystemsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MyLightSystems."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MyLightSystemsFlowHandler:
        return MyLightSystemsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                api_client = MyLightSystemsApiClient(
                    base_url=user_input[CONF_URL],
                    session=async_create_clientsession(self.hass),
                )

                login_response = await api_client.auth(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])

                user_profile = await api_client.get_profile(login_response.token)

                data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_URL: user_input[CONF_URL],
                    CONF_SUBSCRIPTION_ID: user_profile.id,
                    CONF_GRID_TYPE: user_profile.grid_type,
                }

                await self.async_set_unique_id(str(user_profile.id))

                self._abort_if_unique_id_configured()

            except MyLightSystemsInvalidAuthError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except MyLightSystemsConnectionError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MyLightSystemsError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"MyLight Systems ({user_input[CONF_EMAIL]})",
                    data=data,
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
                    vol.Optional(CONF_URL, default=DEFAULT_BASE_URL): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.URL,
                        ),
                    ),
                }
            ),
            errors=_errors,
        )
