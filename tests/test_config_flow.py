"""Tests for MyLight Systems config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_URL
from homeassistant.data_entry_flow import FlowResultType

from custom_components.mylight_systems.api.exceptions import (
    CommunicationError,
    InvalidCredentialsError,
    MyLightSystemsError,
)
from custom_components.mylight_systems.api.models import InstallationDevices, Login, UserProfile
from custom_components.mylight_systems.config_flow import MyLightSystemsFlowHandler
from custom_components.mylight_systems.const import (
    CONF_GRID_TYPE,
    CONF_MASTER_ID,
    CONF_MASTER_RELAY_ID,
    CONF_MASTER_REPORT_PERIOD,
    CONF_SUBSCRIPTION_ID,
    CONF_VIRTUAL_BATTERY_ID,
    CONF_VIRTUAL_DEVICE_ID,
    DOMAIN,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

VALID_USER_INPUT = {
    CONF_EMAIL: "user@example.com",
    CONF_PASSWORD: "s3cr3t",
    CONF_URL: "https://myhome.mylight-systems.com",
}

MOCK_LOGIN = Login(auth_token="tok123")  # noqa: S106
MOCK_PROFILE = UserProfile(subscription_id="sub42", grid_type="one_phase")
MOCK_DEVICES = InstallationDevices(
    master_id="mst1",
    master_report_period=60,
    virtual_device_id="virt1",
    virtual_battery_id="bat1",
    master_relay_id=None,
)

EXISTING_ENTRY_DATA = {
    CONF_EMAIL: "user@example.com",
    CONF_URL: "https://myhome.mylight-systems.com",
    CONF_PASSWORD: "old_password",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_handler(context: dict | None = None) -> MyLightSystemsFlowHandler:
    """Instantiate a flow handler with the minimum HA attributes mocked."""
    handler = MyLightSystemsFlowHandler()
    handler.hass = MagicMock()
    handler.flow_id = "test_flow"
    handler.handler = DOMAIN
    handler.context = context or {}  # ty: ignore[invalid-assignment]
    handler.cur_step = None
    handler._preview = None  # ty: ignore[unresolved-attribute]
    return handler


def make_mock_client(login_exc=None) -> MagicMock:
    """Return a mock API client that succeeds (or raises login_exc on login)."""
    client = MagicMock()
    if login_exc is not None:
        client.async_login = AsyncMock(side_effect=login_exc)
    else:
        client.async_login = AsyncMock(return_value=MOCK_LOGIN)
    client.async_get_profile = AsyncMock(return_value=MOCK_PROFILE)
    client.async_get_devices = AsyncMock(return_value=MOCK_DEVICES)
    return client


def make_mock_entry(data: dict | None = None) -> MagicMock:
    """Return a mock config entry with the given (or default) data."""
    entry = MagicMock()
    entry.data = dict(data or EXISTING_ENTRY_DATA)
    entry.entry_id = "existing_entry_id"
    return entry


# ---------------------------------------------------------------------------
# user step
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_step__shows_form_on_initial_load():
    """No user_input → user form is shown."""
    handler = make_handler()

    result = await handler.async_step_user(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] in (None, {})


@pytest.mark.asyncio
async def test_user_step__creates_entry_on_valid_credentials():
    """Valid credentials result in CREATE_ENTRY with all expected fields."""
    handler = make_handler()
    handler.async_set_unique_id = AsyncMock(return_value=None)  # ty: ignore[invalid-assignment]
    handler._abort_if_unique_id_configured = MagicMock()  # ty: ignore[invalid-assignment]

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(),
        ),
    ):
        result = await handler.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data[CONF_EMAIL] == VALID_USER_INPUT[CONF_EMAIL]
    assert data[CONF_SUBSCRIPTION_ID] == MOCK_PROFILE.subscription_id
    assert data[CONF_GRID_TYPE] == MOCK_PROFILE.grid_type
    assert data[CONF_VIRTUAL_DEVICE_ID] == MOCK_DEVICES.virtual_device_id
    assert data[CONF_VIRTUAL_BATTERY_ID] == MOCK_DEVICES.virtual_battery_id
    assert data[CONF_MASTER_ID] == MOCK_DEVICES.master_id
    assert data[CONF_MASTER_REPORT_PERIOD] == MOCK_DEVICES.master_report_period
    assert data[CONF_MASTER_RELAY_ID] == MOCK_DEVICES.master_relay_id


@pytest.mark.asyncio
async def test_user_step__shows_auth_error_on_invalid_credentials():
    """InvalidCredentialsError shows the form again with error key 'auth'."""
    handler = make_handler()

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=InvalidCredentialsError()),
        ),
    ):
        result = await handler.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_user_step__shows_connection_error_on_communication_failure():
    """CommunicationError shows the form again with error key 'connection'."""
    handler = make_handler()

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=CommunicationError()),
        ),
    ):
        result = await handler.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


@pytest.mark.asyncio
async def test_user_step__shows_unknown_error_on_unexpected_api_error():
    """Generic MyLightSystemsError shows the form again with error key 'unknown'."""
    handler = make_handler()

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=MyLightSystemsError("boom")),
        ),
    ):
        result = await handler.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


# ---------------------------------------------------------------------------
# reauth step
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reauth_confirm__shows_form_on_initial_load():
    """No user_input → reauth_confirm form is shown."""
    handler = make_handler(context={"entry_id": "existing_entry_id", "source": SOURCE_REAUTH})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    result = await handler.async_step_reauth_confirm(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"


@pytest.mark.asyncio
async def test_reauth_confirm__updates_entry_on_valid_new_password():
    """Valid password triggers entry update and flow abort."""
    handler = make_handler(context={"entry_id": "existing_entry_id", "source": SOURCE_REAUTH})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]
    handler.async_update_reload_and_abort = MagicMock(  # ty: ignore[invalid-assignment]
        return_value={"type": FlowResultType.ABORT, "reason": "reauth_successful"}
    )

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(),
        ),
    ):
        result = await handler.async_step_reauth_confirm(user_input={CONF_PASSWORD: "newpass"})

    assert result["type"] == FlowResultType.ABORT
    handler.async_update_reload_and_abort.assert_called_once()  # ty: ignore[unresolved-attribute]


@pytest.mark.asyncio
async def test_reauth_confirm__shows_auth_error_on_invalid_credentials():
    """InvalidCredentialsError shows the reauth form with error key 'auth'."""
    handler = make_handler(context={"entry_id": "existing_entry_id", "source": SOURCE_REAUTH})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=InvalidCredentialsError()),
        ),
    ):
        result = await handler.async_step_reauth_confirm(user_input={CONF_PASSWORD: "wrong"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_reauth_confirm__shows_connection_error_on_communication_failure():
    """CommunicationError shows the reauth form with error key 'connection'."""
    handler = make_handler(context={"entry_id": "existing_entry_id", "source": SOURCE_REAUTH})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=CommunicationError()),
        ),
    ):
        result = await handler.async_step_reauth_confirm(user_input={CONF_PASSWORD: "wrong"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


# ---------------------------------------------------------------------------
# reconfigure step
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reconfigure__shows_form_on_initial_load():
    """No user_input → reconfigure form is shown."""
    handler = make_handler(context={"entry_id": "existing_entry_id"})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    result = await handler.async_step_reconfigure(user_input=None)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


@pytest.mark.asyncio
async def test_reconfigure__aborts_when_entry_not_found():
    """Missing config entry aborts the flow with reason 'not_found'."""
    handler = make_handler(context={"entry_id": "missing_id"})
    handler.hass.config_entries.async_get_entry.return_value = None  # ty: ignore[unresolved-attribute]

    result = await handler.async_step_reconfigure(user_input=None)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "not_found"


@pytest.mark.asyncio
async def test_reconfigure__updates_password_on_valid_input():
    """Valid new password updates the entry and aborts the flow."""
    handler = make_handler(context={"entry_id": "existing_entry_id"})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]
    handler.async_update_reload_and_abort = MagicMock(  # ty: ignore[invalid-assignment]
        return_value={"type": FlowResultType.ABORT, "reason": "reconfigure_successful"}
    )

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(),
        ),
    ):
        result = await handler.async_step_reconfigure(user_input={CONF_PASSWORD: "newpass"})

    assert result["type"] == FlowResultType.ABORT
    handler.async_update_reload_and_abort.assert_called_once()  # ty: ignore[unresolved-attribute]


@pytest.mark.asyncio
async def test_reconfigure__shows_auth_error_on_invalid_credentials():
    """InvalidCredentialsError shows the reconfigure form with error key 'auth'."""
    handler = make_handler(context={"entry_id": "existing_entry_id"})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=InvalidCredentialsError()),
        ),
    ):
        result = await handler.async_step_reconfigure(user_input={CONF_PASSWORD: "wrong"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_reconfigure__shows_connection_error_on_communication_failure():
    """CommunicationError shows the reconfigure form with error key 'connection'."""
    handler = make_handler(context={"entry_id": "existing_entry_id"})
    handler.hass.config_entries.async_get_entry.return_value = make_mock_entry()  # ty: ignore[unresolved-attribute]

    with (
        patch("custom_components.mylight_systems.config_flow.async_create_clientsession"),
        patch(
            "custom_components.mylight_systems.config_flow.MyLightApiClient",
            return_value=make_mock_client(login_exc=CommunicationError()),
        ),
    ):
        result = await handler.async_step_reconfigure(user_input={CONF_PASSWORD: "wrong"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}
