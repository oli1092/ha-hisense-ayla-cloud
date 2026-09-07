"""Conservative property diagnostics shared by HA and the standalone probe."""

from .const import REDACTED

SAFE_VALUES = {"ON", "OFF", "AUTO", "COOL", "HEAT", "DRY", "FAN", "LOW", "MEDIUM", "HIGH", "QUIET", "TURBO"}


def safe_property(prop):
    """Never emit arbitrary cloud strings, objects or unknown property values."""
    name = prop.get("name", "")
    known = name in {
        "t_power", "t_temp", "t_work_mode", "t_fan_speed", "t_fan_leftright",
        "t_fan_power", "t_eco", "t_fan_mute", "t_temp_heatcold", "f_temp_in",
        "f_humidity", "t_control_value", "t_sleep", "t_backlight",
        "f_power_display", "f_votage", "f_electricity",
    }

    def value(item):
        if item is None:
            return None
        if known and (isinstance(item, (bool, int, float)) or
                      isinstance(item, str) and item.upper() in SAFE_VALUES):
            return item
        return REDACTED

    result = {"value": value(prop.get("value"))}
    if prop.get("base_type") in {"integer", "boolean", "decimal", "string"}:
        result["base_type"] = prop["base_type"]
    if isinstance(prop.get("read_only"), bool):
        result["read_only"] = prop["read_only"]
    for key in ("possible_values", "allowed_values", "enum_values"):
        if isinstance(prop.get(key), list):
            result[key] = [value(item) for item in prop[key]]
    return result
