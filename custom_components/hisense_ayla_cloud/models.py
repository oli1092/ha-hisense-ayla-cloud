"""Normalized Ayla models and read-only climate mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import HVAC_MODE_MAP, PROPERTY_POWER, PROPERTY_WORK_MODE

HVAC_OFF = "off"
# Numeric encoding used by the reference integration's AcWorkMode enum.
NUMERIC_HVAC_MODES = {0: "fan_only", 1: "heat", 2: "cool", 3: "dry", 4: "auto"}


def _map_mode(raw: Any) -> str | None:
    if type(raw) is int:
        return NUMERIC_HVAC_MODES.get(raw)
    return HVAC_MODE_MAP.get(raw.upper()) if isinstance(raw, str) else None


@dataclass(slots=True)
class DeviceSnapshot:
    """One successful or failed cloud snapshot."""

    dsn: str
    name: str
    product_name: str
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    available: bool = False
    error: str | None = None

    def value(self, name: str) -> Any:
        """Return the latest value for a property."""

        return self.properties.get(name, {}).get("value")

    def property(self, name: str) -> dict[str, Any]:
        """Return raw metadata for one property."""

        return self.properties.get(name, {})


def _possible_values(prop: dict[str, Any]) -> list[str | int]:
    """Extract enum values across Ayla firmware response variants."""

    for key in ("possible_values", "allowed_values", "enum_values", "values"):
        value = prop.get(key)
        if isinstance(value, list) and all(type(item) in (str, int) for item in value):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
    metadata = prop.get("metadata")
    if isinstance(metadata, dict):
        return _possible_values(metadata)
    return []


def climate_modes(snapshot: DeviceSnapshot) -> list[str]:
    """Map only modes advertised by the cloud property metadata."""

    modes = [HVAC_OFF] if PROPERTY_POWER in snapshot.properties else []
    stored = _map_mode(snapshot.value(PROPERTY_WORK_MODE))
    for raw in _possible_values(snapshot.property(PROPERTY_WORK_MODE)):
        mapped = _map_mode(raw)
        if mapped and mapped not in modes:
            modes.append(mapped)
    if stored and stored not in modes:
        modes.append(stored)
    current = climate_hvac_mode(snapshot)
    if current and current not in modes:
        modes.append(current)
    return modes


def climate_hvac_mode(snapshot: DeviceSnapshot) -> str | None:
    """Map current cloud values to Home Assistant HVAC modes."""

    power = snapshot.value(PROPERTY_POWER)
    if (type(power) in (bool, int) and power == 0) or (
        isinstance(power, str) and power.upper() in ("OFF", "0")
    ):
        return HVAC_OFF
    raw = snapshot.value(PROPERTY_WORK_MODE)
    return _map_mode(raw)


def target_temperature(snapshot: DeviceSnapshot) -> float | None:
    """Decode the packed Celsius field verified against all three EU devices."""
    raw = snapshot.value("t_temp")
    if type(raw) in (int, float):
        return float(raw)
    control = snapshot.value("t_control_value")
    if type(control) is int and 0 <= control <= 0xFFFFFFFF:
        if control & (1 << 31):
            return None
        return float((control >> 17) & 63)
    return None
