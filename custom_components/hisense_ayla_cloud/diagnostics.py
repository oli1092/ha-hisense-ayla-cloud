"""Redacted diagnostics for the read-only prototype."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_EMAIL, CONF_REFRESH_TOKEN, REDACTED
from .coordinator import HisenseCoordinator


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
                "name": snapshot.name,
                "product_name": snapshot.product_name,
                "available": snapshot.available,
                "error": snapshot.error,
                "properties": {
                    name: _safe_property(prop) for name, prop in snapshot.properties.items()
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


def _safe_property(prop: dict[str, Any]) -> dict[str, Any]:
    """Keep useful raw metadata while excluding arbitrary secret fields."""

    allowed = {
        "name",
        "value",
        "base_type",
        "read_only",
        "direction",
        "possible_values",
        "allowed_values",
        "enum_values",
        "metadata",
        "updated_at",
    }
    safe = {key: value for key, value in prop.items() if key in allowed}
    if isinstance(safe.get("metadata"), dict):
        metadata = safe["metadata"]
        safe["metadata"] = {
            key: value
            for key, value in metadata.items()
            if key in {"values", "possible_values", "allowed_values", "enum_values"}
        }
    return safe
