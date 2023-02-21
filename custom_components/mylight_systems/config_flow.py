"""Adds config flow for mylight_systems."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api.client import MyLightApiClient
from .api.exceptions import (
    CommunicationException,
    InvalidCredentialsException,
    MyLightSystemsException,
)
from .const import (
    CONF_GRID_TYPE,
    CONF_MASTER_ID,
    CONF_MASTER_REPORT_PERIOD,
    CONF_SUBSCRIPTION_ID,
    CONF_VIRTUAL_BATTERY_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
    LOGGER,
)


class MyLightSystemsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MyLightSystems."""

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
                api_client = MyLightApiClient(
                    session=async_create_clientsession(self.hass),
                )

                login_response = await api_client.async_login(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )

                user_profile = await api_client.async_get_profile(
                    login_response.auth_token
                )
                device_ids = await api_client.async_get_devices(
                    login_response.auth_token
                )

                data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_SUBSCRIPTION_ID: user_profile.subscription_id,
                    CONF_GRID_TYPE: user_profile.grid_type,
                    CONF_VIRTUAL_DEVICE_ID: device_ids.virtual_device_id,
                    CONF_VIRTUAL_BATTERY_ID: device_ids.virtual_battery_id,
                    CONF_MASTER_ID: device_ids.master_id,
                    CONF_MASTER_REPORT_PERIOD: device_ids.master_report_period,
                }

                await self.async_set_unique_id(
                    str(user_profile.subscription_id)
                )

                self._abort_if_unique_id_configured()

            except InvalidCredentialsException as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except CommunicationException as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MyLightSystemsException as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_profile.subscription_id,
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
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )
