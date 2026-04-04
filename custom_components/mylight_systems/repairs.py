"""Repair flows for MyLight Systems."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict | None) -> RepairsFlow:
    """Create a repair fix flow for the given issue."""
    if issue_id == "auth_failed":
        return AuthFailedRepairFlow(data)
    raise ValueError(f"Unknown issue: {issue_id}")


class AuthFailedRepairFlow(RepairsFlow):
    """Repair flow that starts the reauth flow for the affected config entry."""

    def __init__(self, data: dict | None) -> None:
        """Initialize."""
        self._entry_id: str | None = (data or {}).get("entry_id")

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle the first step."""
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Show confirmation and start reauth when confirmed."""
        if user_input is not None:
            if self._entry_id:
                entry = self.hass.config_entries.async_get_entry(self._entry_id)
                if entry:
                    entry.async_start_reauth(self.hass)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))
