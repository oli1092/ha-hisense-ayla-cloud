"""Redacted diagnostics for the read-only prototype."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_EMAIL, CONF_REFRESH_TOKEN, REDACTED
from .coordinator import HisenseCoordinator
from .safe_diagnostics import safe_property


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return useful property metadata without credentials or identifiers."""

    coordinator: HisenseCoordinator = entry.runtime_data
    devices: list[dict[str, Any]] = []
    for snapshot in (coordinator.data or {}).values():
        devices.append(
            {
                "dsn": REDACTED,
                "name": REDACTED,
                "product_name": REDACTED,
                "available": snapshot.available,
                "error": snapshot.error,
                "properties": {
                    name: safe_property(prop) for name, prop in snapshot.properties.items()
                },
            }
        )
    return {
        "entry": {
            "entry_id": entry.entry_id,
            "app_code": entry.data.get("app_code"),
            "email": REDACTED if entry.data.get(CONF_EMAIL) else None,
            "refresh_token": REDACTED if entry.data.get(CONF_REFRESH_TOKEN) else None,
        },
        "devices": devices,
        "cloud_only": True,
        "local_callback": False,
        "local_ip_access": False,
    }
